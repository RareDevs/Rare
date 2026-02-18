#!/usr/bin/env python3

# AI Disclosure: Some source code modifications in this file are AI-generated, but also human-reviewed and tested.

import logging
import os
import signal
import subprocess
import sys
from argparse import Namespace
from ctypes import CDLL, c_int, c_void_p
from ctypes.util import find_library
from logging import getLogger
from pathlib import Path
from typing import Any, Generator, List

# Constants defined in sys/procctl.h
P_PID = 0
PROC_REAP_ACQUIRE = 2


def get_libc() -> str:
    """Find libc.so from the user's system."""
    return find_library("c") or ""


def _get_pids() -> Generator[int, Any, None]:
    # FreeBSD's /proc is often not mounted. If it is, entries are just PIDs.
    proc_path = Path("/proc")
    if proc_path.exists():
        yield from (int(p.name) for p in proc_path.glob("*") if p.name.isdigit())
    else:
        # Fallback: Use ps to get PIDs if /proc isn't available
        out = subprocess.check_output(["ps", "-ax", "-o", "pid"])
        for line in out.splitlines()[1:]:
            yield int(line.strip())


def get_pstree_from_pid(root_pid: int) -> set[int]:
    """Get descendent PIDs. Uses 'ps' for better FreeBSD compatibility."""
    descendants: set[int] = set()

    try:
        # -o ppid,pid gets parent and child PIDs
        out = subprocess.check_output(["ps", "-ax", "-o", "ppid,pid"], encoding="utf-8")
        lines = out.strip().split("\n")[1:]
        pid_to_ppid = {}
        for line in lines:
            ppid, pid = map(int, line.split())
            pid_to_ppid[pid] = ppid
    except Exception:
        return descendants

    current_pid: list[int] = [root_pid]
    while current_pid:
        current = current_pid.pop()
        # Ignore. mypy flags [arg-type] due to the reuse of pid variable
        for pid, ppid in pid_to_ppid.items():  # type: ignore
            if ppid == current and pid not in descendants:
                descendants.add(pid)  # type: ignore
                current_pid.append(pid)  # type: ignore

    return descendants


def subreaper(args: Namespace, other: List[str]) -> int:
    logger = getLogger("subreaper")
    logging.basicConfig(
        format="[%(name)s] %(levelname)s: %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
        stream=sys.stderr,
    )

    logger.debug("command: %s", args)
    logger.debug("arguments: %s", other)

    def signal_handler(sig, frame):
        logger.info("Caught '%s' signal.", signal.strsignal(sig))
        pstree = get_pstree_from_pid(os.getpid())
        for p in pstree:
            try:
                os.kill(p, sig)
            except ProcessLookupError:
                continue

    command: List[str] = [args.command, *other]
    workdir: str = args.workdir
    child_status: int = 0

    libc_path: str = get_libc()
    if not libc_path:
        logger.error("Could not find libc")
        return 1
    libc: CDLL = CDLL(libc_path)

    # Acquire Reaper Status
    # FreeBSD equivalent of PR_SET_CHILD_SUBREAPER
    # procctl(P_PID, getpid(), PROC_REAP_ACQUIRE, NULL)
    procctl = libc.procctl
    # procctl.restype = c_int
    procctl.argtypes = [
        c_int,
        c_int,
        c_int,
        c_void_p,
    ]

    # Set Process Name (FreeBSD specific)
    # FreeBSD prefers setproctitle over prctl for naming
    proc_name = b"reaper"
    try:
        libc.setproctitle(proc_name)
    except AttributeError:
        logger.debug("setproctitle not found in libc")

    procctl_res = procctl(P_PID, os.getpid(), PROC_REAP_ACQUIRE, None)
    logger.debug("procctl PROC_REAP_ACQUIRE exited with status: %s", procctl_res)

    pid = os.fork()  # pylint: disable=E1101
    if pid == -1:
        logger.error("Fork failed")

    if pid == 0:
        os.chdir(workdir)
        os.execvp(command[0], command)  # noqa: S606
    else:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            child_pid, child_status = os.wait()  # pylint: disable=E1101
            logger.info("Child %s exited with status: %s", child_pid, child_status)
        except ChildProcessError as e:
            logger.info(e)
            break

    return child_status


if __name__ == "__main__":
    sep = sys.argv.index("--")
    argv = sys.argv[sep + 1 :]
    args = Namespace(command=argv.pop(0), workdir=os.getcwd(), debug=True)
    subreaper(args, argv)


__all__ = ["subreaper"]

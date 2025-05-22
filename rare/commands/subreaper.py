import logging
import os
import sys
from argparse import Namespace
from ctypes import CDLL, c_int, c_ulong
from ctypes.util import find_library
from logging import getLogger
from typing import List

# Constant defined in prctl.h
# See prctl(2) for more details
PR_SET_CHILD_SUBREAPER = 36


def get_libc() -> str:
    """Find libc.so from the user's system."""
    return find_library("c") or ""


def subreaper(args: Namespace, other: List[str]) -> int:
    logger = getLogger("subreaper")
    logging.basicConfig(
        format="[%(name)s] %(levelname)s: %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
        stream=sys.stderr,
    )

    command: List[str] = [args.command, *other]
    workdir: str = args.workdir
    wait_status: int = 0

    libc: str = get_libc()
    prctl = CDLL(libc).prctl
    prctl.restype = c_int
    prctl.argtypes = [
        c_int,
        c_ulong,
        c_ulong,
        c_ulong,
        c_ulong,
    ]
    prctl_ret = prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0, 0)
    logger.debug("prctl exited with status: %s", prctl_ret)

    pid = os.fork()  # pylint: disable=E1101
    if pid == -1:
        logger.error("Fork failed")

    if pid == 0:
        sys.stdout.flush()
        sys.stderr.flush()
        os.chdir(workdir)
        os.execvp(command[0], command)  # noqa: S606

    while True:
        try:
            wait_pid, wait_status = os.wait()  # pylint: disable=E1101
            logger.info("Child %s exited with wait status: %s", wait_pid, wait_status)
        except ChildProcessError as e:
            logger.info(e)
            break

    return wait_status


__all__ = ["subreaper"]
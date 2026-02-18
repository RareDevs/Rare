#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def log(msg: Any):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


def run_proc(args: List, env: Dict):
    return subprocess.call(args, env=env, stderr=sys.stderr, stdout=sys.stdout)


if __name__ == "__main__":
    if "STEAM_COMPAT_DATA_PATH" not in os.environ:
        log("No compat data path?")
        sys.exit(1)

    wine_bin = "/usr/bin/wine"
    wineserver_bin = "/usr/bin/wineserver"

    compat_data = Path(os.environ["STEAM_COMPAT_DATA_PATH"]).resolve(strict=False)
    compat_data.mkdir(parents=True, exist_ok=True)
    compat_data.joinpath("creation_sync_guard").touch(exist_ok=True)
    compat_data.joinpath("tracked_files").touch(exist_ok=True)

    wine_prefix = compat_data.joinpath("pfx").resolve(strict=False)
    if not wine_prefix.exists():
        wine_prefix.mkdir(parents=True, exist_ok=True)

    dlls = {
        "d3d8": "n,b",
        "d3d9": "n,b",
        "dxgi": "n,b",
        "d3d10core": "n,b",
        "d3d11": "n,b",
        "d3d12": "n,b;",
        "d3d12core": "n,b",
    }
    dlloverrides = ";".join(("=".join((k , v)) for k, v in dlls.items()))
    dlloverrides = ";".join((os.environ.get("WINEDLLOVERRIDES", ""), dlloverrides))

    env = {
        "WINE": wine_bin,
        "WINEPREFIX": wine_prefix.as_posix(),
        "WINEDLLOVERRIDES": dlloverrides,
    }
    log(env)

    local_env = os.environ.copy()
    local_env.update(env)

    #determine mode
    rc = 0
    if sys.argv[1] == "run":
        #start target app
        rc = run_proc([wine_bin] + sys.argv[2:], local_env)
    elif sys.argv[1] == "waitforexitandrun":
        #wait for wineserver to shut down
        run_proc([wineserver_bin, "-w"], local_env)
        #then run
        rc = run_proc([wine_bin] + sys.argv[2:], local_env)
    elif sys.argv[1] == "runinprefix":
        rc = run_proc([wine_bin] + sys.argv[2:], local_env)
    elif sys.argv[1] == "getcompatpath":
        #linux -> windows path
        path = subprocess.check_output([wine_bin, "winepath", "-w", sys.argv[2]], env=local_env, stderr=sys.stderr)
        sys.stdout.buffer.write(path)
        sys.stdout.buffer.flush()
        sys.stderr.buffer.flush()
    elif sys.argv[1] == "getnativepath":
        #windows -> linux path
        path = subprocess.check_output([wine_bin, "winepath", sys.argv[2]], env=local_env, stderr=sys.stderr)
        sys.stdout.buffer.write(path)
        sys.stdout.buffer.flush()
        sys.stderr.buffer.flush()
    else:
        log("Need a verb.")
        sys.exit(1)

    sys.exit(rc)

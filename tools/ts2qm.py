#!/usr/bin/env python3
import os
import shlex
import sys
from pathlib import Path

basedir = Path(__file__).parent.parent.joinpath("rare/resources/languages/")
venv_bin_path = Path(sys.executable).parent

for f in basedir.iterdir():
    if f.suffix == ".ts" and f.name != "source.ts":
        command = shlex.join(
            (
                "pyside6-lrelease",
                "-compress",
                "-removeidentical",
                f.as_posix(),
            )
        )
        os.system(f"PATH={venv_bin_path}:" + os.environ.get("PATH", "") + " " + command)

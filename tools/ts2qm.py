#!/usr/bin/env python3
import os
import shlex
import subprocess
from pathlib import Path

basedir = Path(__file__).parent.parent.joinpath("rare/resources/languages/")

for f in basedir.iterdir():
    if f.suffix == ".ts" and f.name != "source.ts":
        subprocess.run(
            shlex.join(
                (
                    "pyside6-lrelease",
                    "-compress",
                    "-removeidentical",
                    f.as_posix(),
                )
            ),
            check=False
        )

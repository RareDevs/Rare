#!/usr/bin/env python3
import os
import shlex
from pathlib import Path

basedir = Path(__file__).parent.parent.joinpath("rare/resources/languages/")

for f in basedir.iterdir():
    if f.suffix == ".ts" and f.name != "source.ts":
        os.system(
            shlex.join(
                (
                    "/home/alessio/Progetti/Rare/build_venv/bin/pyside6-lrelease",
                    "-compress",
                    "-removeidentical",
                    f.as_posix(),
                )
            )
        )

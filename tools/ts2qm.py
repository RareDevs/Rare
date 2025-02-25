#!/usr/bin/env python3
import os
import shlex

for f in os.listdir(os.path.join(os.path.dirname(__file__), "../rare/resources/languages/")):
    if f.endswith(".ts") and f != "source.ts":
        os.system(shlex.join((
            "pyside6-lrelease",
            "-compress",
            "-removeidentical",
            f"{os.path.join(os.path.dirname(__file__), '../rare/resources/languages/', f)}",
        )))

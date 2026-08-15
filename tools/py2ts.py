#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

basedir = Path(__file__).parent.parent.joinpath('rare')

py_files: list[Path] = []
for root, dirs, files in os.walk(basedir):
    if '__pycache__' in dirs:
        dirs.remove('__pycache__')
    if 'rare/resources' in root:
        continue
    candidates = (f for f in files if f.endswith(('py', '.ui')))
    for c in candidates:
        py_files.append(Path(root).joinpath(c))

py_files = sorted(py_files)

if py_files:
    subprocess.run(
        [
            'pyside6-lupdate',
            '-noobsolete',
            '-locations', 'absolute',
            *(f.as_posix() for f in py_files),
            '-ts', f'{basedir.as_posix()}/resources/languages/source.ts',
        ],
        check=False,
    )

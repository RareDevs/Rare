#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

python -m pylint -E rare --jobs=1 --disable=E0611,E1123,E1120 --ignore=ui,singleton.py --extension-pkg-whitelist=PyQt5 --generated-members=PyQt5.*

cd "$cwd" || exit

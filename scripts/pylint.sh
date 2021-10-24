#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

pylint -E rare --jobs=3 --disable=E0611,E1123,E1120 --ignore=ui,singleton.py --extension-pkg-whitelist=PyQt5

cd "$cwd" || exit

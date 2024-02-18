#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

#py_files=$(find rare -iname "*.py" -not -path rare/ui)
#ui_files=$(find rare/ui -iname "*.ui")

pylupdate5 -noobsolete $(find rare/ -iname "*.py") -ts rare/resources/languages/source.ts

cd "$cwd" || exit

#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

pylupdate5 -noobsolete $(find rare/ -iname "*.py") -ts rare/resources/languages/placeholder.ts

cd "$cwd" || exit

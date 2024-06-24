#!/usr/bin/env bash

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

# shellcheck disable=SC2046
pyside6-lupdate -noobsolete $(find rare/ -iname "*.py") -ts rare/resources/languages/source.ts

cd "$cwd" || exit

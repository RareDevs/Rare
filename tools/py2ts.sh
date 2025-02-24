#!/usr/bin/env bash

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

# shellcheck disable=SC2046
readarray -d '' files < <(find rare -not -path "rare/resources/*" \( -iname "*.py" -or -iname "*.ui" \) -print0)
pyside6-lupdate \
  -noobsolete \
  -locations absolute \
  "${files[@]}" \
  -ts rare/resources/languages/source.ts

cd "$cwd" || exit

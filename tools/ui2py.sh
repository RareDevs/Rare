#!/usr/bin/env bash

if [ -n "${1}" ]; then
    if [ ! -f "${1}" ]; then
      echo "${1} does not exist"
      exit 0
    fi
    echo "Generating python file for ${1}"
    pyside6-uic "${1}" -a -o "${1%.ui}.py"
    exit 0
fi

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

changed="$(git diff --name-only HEAD | grep '\.ui')"

for ui in $changed; do
    if [ ! -f "$ui" ]; then
      echo "$ui does not exist. Skipping"
      continue
    fi
    echo "Generating python file for ${ui}"
    pyside6-uic "${ui}" -a -o "${ui%.ui}.py"
done

cd "$cwd" || exit

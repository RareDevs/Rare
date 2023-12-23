#!/bin/sh

if [ -n "${1}" ]; then
    if [ ! -f "${1}" ]; then
      echo "${1} does not exist"
      exit 0
    fi
    echo "Generating python file for ${1}"
    pyuic5 "${1}" -x -o "${1%.ui}.py"
    sed '/QtCore.QMetaObject.connectSlotsByName/d' -i "${1%.ui}.py"
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
    pyuic5 "${ui}" -x -o "${ui%.ui}.py"
    sed '/QtCore.QMetaObject.connectSlotsByName/d' -i "${ui%.ui}.py"
done

cd "$cwd" || exit

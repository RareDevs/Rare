#!/bin/sh

if [ ! -z "${1}" ]; then
    echo "Generating python file for ${1}"
    pyuic5 "${1}" -x -o "${1%.ui}.py"
    exit 0
fi

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

changed="$(git diff --name-only HEAD | grep '\.ui')"

for ui in $changed; do
    echo "Generating python file for ${ui}"
    pyuic5 "${ui}" -x -o "${ui%.ui}.py"
    sed '/QtCore.QMetaObject.connectSlotsByName/d' -i "${ui%.ui}.py"
done

cd "$cwd" || exit

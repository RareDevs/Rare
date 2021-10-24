#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

changed="$(git diff --name-only HEAD | grep '\.ui')"

for ui in $changed; do
    echo "Generating python file for ${ui}"
    pyuic5 "${ui}" -x -o "${ui%.ui}.py"
done

cd "$cwd" || exit

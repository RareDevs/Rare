#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/../ || exit

pyrcc5 rare/resources/resources.qrc -o rare/resources/resources.py

cd "$cwd" || exit

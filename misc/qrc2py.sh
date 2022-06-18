#!/bin/sh

cwd="$(pwd)"
cd "$(dirname "$0")"/../ || exit

pyrcc5 -compress 6 \
    rare/resources/resources.qrc \
    -o rare/resources/resources.py
pyrcc5 -compress 6 \
    rare/resources/stylesheets/RareStyle/stylesheet.qrc \
    -o rare/resources/stylesheets/RareStyle/__init__.py
pyrcc5 -compress 6 \
    rare/resources/stylesheets/ChildOfMetropolis/stylesheet.qrc \
    -o rare/resources/stylesheets/ChildOfMetropolis/__init__.py

cd "$cwd" || exit

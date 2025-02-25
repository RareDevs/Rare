#!/usr/bin/env bash
_rcc_cmd="pyside6-rcc --compress 6 --compress-algo zlib --threshold 0"

cwd="$(pwd)"
cd "$(dirname "${0}")"/../ || exit

force=0
if [[ "$1" == "--force" ]]
then
  force=1
fi

resources=(
  "rare/resources/images/"
  "rare/resources/colors/"
  "rare/resources/resources.qrc"
)

resources_changed=0
for r in "${resources[@]}"
do
  if [[ $(git diff --name-only HEAD "$r") ]]
  then
    resources_changed=1
  fi
done

if [[ $resources_changed -eq 1 || $force -eq 1 ]]
then
  echo "Re-compiling main resources"
  $_rcc_cmd \
      rare/resources/resources.qrc \
      -o rare/resources/resources.py
fi

if [[ $force -eq 1 ]]
then
  echo "Re-compiling static_css resources"
  $_rcc_cmd \
      rare/resources/static_css/stylesheet.qrc \
      -o rare/resources/static_css/__init__.py
fi

if [[ $(git diff --name-only HEAD "rare/resources/stylesheets/RareStyle/") || $force -eq 1 ]]
then
  echo "Re-compiling RareStyle stylesheet resources"
  $_rcc_cmd \
      rare/resources/stylesheets/RareStyle/stylesheet.qrc \
      -o rare/resources/stylesheets/RareStyle/__init__.py
fi


if [[ $(git diff --name-only HEAD "rare/resources/stylesheets/ChildOfMetropolis/") || $force -eq 1 ]]
then
  echo "Re-compiling ChildOfMetropolis stylesheet resources"
  $_rcc_cmd \
      rare/resources/stylesheets/ChildOfMetropolis/stylesheet.qrc \
      -o rare/resources/stylesheets/ChildOfMetropolis/__init__.py
fi


cd "$cwd" || exit

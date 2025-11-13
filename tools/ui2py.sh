#!/usr/bin/env bash

_uic_cmd() {
    python3 tools/run_uic.py "${ui}"
}

force=0
if [[ "${1}" == "--force" ]]
then
    force=1
elif [ -n "${1}" ]; then
    if [ ! -f "${1}" ]; then
      echo "${1} does not exist"
      exit 0
    fi
    _uic_cmd "${1}"
    exit 0
fi

cwd="$(pwd)"
cd "$(dirname "$0")"/.. || exit

changed="$(git diff --name-only HEAD | grep '\.ui')"
if [[  $force -eq 1 ]]
then
    changed=$(find ./rare/ui -iname "*.ui")
fi

for ui in $changed; do
    if [ ! -f "${ui}" ]; then
      echo "${ui} does not exist. Skipping"
      continue
    fi
    _uic_cmd "${ui}"
done

cd "${cwd}" || exit

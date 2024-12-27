#!/usr/bin/env bash

nuitka_opts=(
    '--output-dir=nuitka.workdir'
    '--assume-yes-for-downloads'
    '--show-scons'
    '--clang'
    '--lto=no'
    '--jobs=4'
    '--static-libpython=no'
    '--standalone'
    '--enable-plugin=anti-bloat'
    '--enable-plugin=pyside6'
    '--show-modules'
    '--show-anti-bloat-changes'
    '--follow-stdlib'
    '--follow-imports'
    '--nofollow-import-to="*.tests"'
    '--nofollow-import-to="*.distutils"'
    '--nofollow-import-to="distutils"'
    '--nofollow-import-to="unittest"'
    '--nofollow-import-to="pydoc"'
    '--nofollow-import-to="tkinter"'
    '--nofollow-import-to="test"'
    '--prefer-source-code'
    '--include-package=pypresence'
    '--include-package-data=qtawesome'
    '--include-data-dir=rare/resources/images/=rare/resources/images/'
    '--include-data-files=rare/resources/languages/rare_*.qm=rare/resources/languages/'
    '--output-filename=Rare.bin'
    '--file-description=Rare.bin'
    '--company-name=RareDevs'
    '--product-name=Rare'
    '--file-version=0.0.0.0'
    '--product-version=0.0.0.0'
)

python -m nuitka "${nuitka_opts[@]}" rare

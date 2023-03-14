#!/usr/bin/bash

python -m nuitka \
--assume-yes-for-downloads \
--mingw64 \
--lto=no \
--jobs=2 \
--static-libpython=no \
--standalone \
--enable-plugin=anti-bloat \
--enable-plugin=pyside6 \
--show-modules \
--show-anti-bloat-changes \
--follow-stdlib \
--follow-imports \
--nofollow-import-to="*.tests" \
--nofollow-import-to="*.distutils" \
--nofollow-import-to="distutils" \
--nofollow-import-to="unittest" \
--nofollow-import-to="pydoc" \
--nofollow-import-to="tkinter" \
--nofollow-import-to="test" \
--prefer-source-code \
--include-package=pypresence \
--include-package-data=qtawesome \
--include-data-dir=rare/resources/images=rare/resources/images \
--include-data-files=rare/resources/languages=rare/resources/languages="*.qm" \
--windows-icon-from-ico=rare/resources/images/Rare.ico \
--windows-company-name=Rare \
--windows-product-name=Rare \
--windows-file-description=rare.exe \
--windows-file-version=0.0.0.0 \
--windows-product-version=0.0.0.0 \
--enable-console \
rare

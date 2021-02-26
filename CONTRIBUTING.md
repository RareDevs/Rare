# Contributing

## What you can do

### Add translations

1. Execute ```pylupdate5 $(find -name "*.py") -ts Rare/languages/{your lang (two letters)}.ts``` in project directrory
2. Modify the .ts file manually or in Qt Linguist
3. Compile the file with ```lrelease Rare/languages/{lang}.ts```
4. Create a Pull request

### Add Stylesheets

For this you can create a .qss file in Rare/Styles/ directory or modify the existing RareStyle.qss file. Here are some
exmples:
[Qt Docs](https://doc.qt.io/qt-5/stylesheet-examples.html)

### Add features

Select one Feature of the Todo list or improve the code. Then you can create a Pull request

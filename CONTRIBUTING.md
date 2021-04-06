# Contributing

## What you can do

To Contribute first fork the repository

### Add translations

1. Execute ```pylupdate5 $(find -name "*.py") -ts Rare/languages/{your lang (two letters)}.ts``` in project directrory
2. Modify the .ts file manually or in Qt Linguist
3. Compile the file with ```lrelease Rare/languages/{lang}.ts```

### Add Stylesheets

For this you can create a .qss file in Rare/Styles/ directory or modify the existing RareStyle.qss file. Here are some
exmples:
[Qt Docs](https://doc.qt.io/qt-5/stylesheet-examples.html)

### Add features

Select one Card of the project and implement it or make other changes


If you made your changes, create a pull request

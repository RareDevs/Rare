"""Python adaptation of https://github.com/dridk/QJsonModel

Supports Python 2 and 3 with PySide, PySide2, PyQt4 or PyQt5.
Requires https://github.com/mottosso/Qt.py

Usage:
    Use it like you would the C++ version.

    >>> import qjsonmodel
    >>> model = qjsonmodel.QJsonModel()
    >>> model.load({"key": "value"})

Test:
    Run the provided example to sanity check your Python,
    dependencies and Qt binding.

    $ python qjsonmodel.py

Changes:
    This module differs from the C++ version in the following ways.

    1. Setters and getters are replaced by Python properties
    2. Objects are sorted by default, disabled via load(sort=False)
    3. load() takes a Python dictionary as opposed to
       a string or file handle.

        - To load from a string, use built-in `json.loads()`
            >>> import json
            >>> document = json.loads("{'key': 'value'}")
            >>> model.load(document)

        - To load from a file, use `with open(fname)`
              >>> import json
              >>> with open("file.json") as f:
              ...    document = json.load(f)
              ...    model.load(document)

"""

import json

from PyQt5 import QtCore, QtWidgets


class QJsonTreeItem(object):
    def __init__(self, parent=None):
        self._parent = parent

        self._key = ""
        self._value = ""
        self._type = None
        self._children = list()

    def appendChild(self, item):
        self._children.append(item)

    def child(self, row):
        return self._children[row]

    def parent(self):
        return self._parent

    def childCount(self):
        return len(self._children)

    def row(self):
        return (
            self._parent._children.index(self)
            if self._parent else 0
        )

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, typ):
        self._type = typ

    @classmethod
    def load(self, value, parent=None, sort=True):
        rootItem = QJsonTreeItem(parent)
        rootItem.key = "root"

        if isinstance(value, dict):
            items = (
                sorted(value.items())
                if sort else value.items()
            )

            for key, value in items:
                child = self.load(value, rootItem)
                child.key = key
                child.type = type(value)
                rootItem.appendChild(child)

        elif isinstance(value, list):
            for index, value in enumerate(value):
                child = self.load(value, rootItem)
                child.key = index
                child.type = type(value)
                rootItem.appendChild(child)

        else:
            rootItem.value = value
            rootItem.type = type(value)

        return rootItem


class QJsonModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(QJsonModel, self).__init__(parent)

        self._rootItem = QJsonTreeItem()
        self._headers = ("key", "value")

    def clear(self):
        self.load({})

    def load(self, document):
        """Load from dictionary

        Arguments:
            document (dict): JSON-compatible dictionary

        """

        assert isinstance(document, (dict, list, tuple)), (
                "`document` must be of dict, list or tuple, "
                "not %s" % type(document)
        )

        self.beginResetModel()

        self._rootItem = QJsonTreeItem.load(document)
        self._rootItem.type = type(document)

        self.endResetModel()

        return True

    def json(self, root=None):
        """Serialise model as JSON-compliant dictionary

        Arguments:
            root (QJsonTreeItem, optional): Serialise from here
                defaults to the the top-level item

        Returns:
            model as dict

        """

        root = root or self._rootItem
        return self.genJson(root)

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.key

            if index.column() == 1:
                return item.value

        elif role == QtCore.Qt.EditRole:
            if index.column() == 1:
                return item.value

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            if index.column() == 1:
                item = index.internalPointer()
                item.value = str(value)

                self.dataChanged.emit(index, index, [QtCore.Qt.EditRole])

                return True

        return False

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            return self._headers[section]

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    def flags(self, index):
        flags = super(QJsonModel, self).flags(index)

        if index.column() == 1:
            return QtCore.Qt.ItemIsEditable | flags
        else:
            return flags

    def genJson(self, item):
        nchild = item.childCount()

        if item.type is dict:
            document = {}
            for i in range(nchild):
                ch = item.child(i)
                document[ch.key] = self.genJson(ch)
            return document

        elif item.type == list:
            document = []
            for i in range(nchild):
                ch = item.child(i)
                document.append(self.genJson(ch))
            return document

        else:
            return item.value


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    view = QtWidgets.QTreeView()
    model = QJsonModel()

    view.setModel(model)

    document = json.loads("""\
    {
        "firstName": "John",
        "lastName": "Smith",
        "age": 25,
        "address": {
            "streetAddress": "21 2nd Street",
            "city": "New York",
            "state": "NY",
            "postalCode": "10021"
        },
        "phoneNumber": [
            {
                "type": "home",
                "number": "212 555-1234"
            },
            {
                "type": "fax",
                "number": "646 555-4567"
            }
        ]
    }
    """)

    model.load(document)
    model.clear()
    model.load(document)

    # Sanity check
    assert (
            json.dumps(model.json(), sort_keys=True) ==
            json.dumps(document, sort_keys=True)
    )

    view.show()
    view.resize(500, 300)
    app.exec_()

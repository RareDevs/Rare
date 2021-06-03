import sys
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtWidgets import QApplication, QCompleter, QLineEdit

def get_data(model):
    model.setStringList(["completion", "data", "goes", "here"])

if __name__ == "__main__":

    app = QApplication(sys.argv)
    edit = QLineEdit()
    completer = QCompleter()
    edit.setCompleter(completer)

    model = QStringListModel()
    completer.setModel(model)
    get_data(model)

    edit.show()
    sys.exit(app.exec_())
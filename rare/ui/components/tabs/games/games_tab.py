# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/games/games_tab.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtWidgets


class Ui_GamesTab(object):
    def setupUi(self, GamesTab):
        GamesTab.setObjectName("GamesTab")
        GamesTab.resize(1071, 678)
        GamesTab.setWindowTitle("StackedWidget")
        self.games = QtWidgets.QWidget()
        self.games.setObjectName("games")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.games)
        self.verticalLayout.setObjectName("verticalLayout")
        self.game_list_scroll_area = QtWidgets.QScrollArea(self.games)
        self.game_list_scroll_area.setWidgetResizable(True)
        self.game_list_scroll_area.setObjectName("game_list_scroll_area")
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setGeometry(QtCore.QRect(0, 0, 1051, 658))
        self.scroll_widget.setObjectName("scroll_widget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.scroll_widget)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.count_games_label = QtWidgets.QLabel(self.scroll_widget)
        self.count_games_label.setText("")
        self.count_games_label.setObjectName("count_games_label")
        self.verticalLayout_4.addWidget(self.count_games_label)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_4.addItem(spacerItem)
        self.game_list_scroll_area.setWidget(self.scroll_widget)
        self.verticalLayout.addWidget(self.game_list_scroll_area)
        GamesTab.addWidget(self.games)

        self.retranslateUi(GamesTab)
        QtCore.QMetaObject.connectSlotsByName(GamesTab)

    def retranslateUi(self, GamesTab):
        pass


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    GamesTab = QtWidgets.QStackedWidget()
    ui = Ui_GamesTab()
    ui.setupUi(GamesTab)
    GamesTab.show()
    sys.exit(app.exec_())

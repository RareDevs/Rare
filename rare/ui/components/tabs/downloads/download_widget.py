
################################################################################
## Form generated from reading UI file 'download_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QPushButton, QSizePolicy


class Ui_DownloadWidget:
    def setupUi(self, DownloadWidget):
        if not DownloadWidget.objectName():
            DownloadWidget.setObjectName("DownloadWidget")
        DownloadWidget.resize(479, 86)
        DownloadWidget.setWindowTitle("DownloadWidget")
        self.active_download_layout = QGridLayout(DownloadWidget)
        self.active_download_layout.setObjectName("active_download_layout")
        self.active_download_layout.setContentsMargins(0, 0, 0, 0)
        self.dl_name = QLabel(DownloadWidget)
        self.dl_name.setObjectName("dl_name")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dl_name.sizePolicy().hasHeightForWidth())
        self.dl_name.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(False)
        self.dl_name.setFont(font)
        self.dl_name.setText("dl_name")

        self.active_download_layout.addWidget(self.dl_name, 0, 1, 1, 3)

        self.dl_name_label = QLabel(DownloadWidget)
        self.dl_name_label.setObjectName("dl_name_label")
        font1 = QFont()
        font1.setBold(True)
        self.dl_name_label.setFont(font1)
        self.dl_name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.active_download_layout.addWidget(self.dl_name_label, 0, 0, 1, 1)

        self.cache_used = QLabel(DownloadWidget)
        self.cache_used.setObjectName("cache_used")
        sizePolicy.setHeightForWidth(self.cache_used.sizePolicy().hasHeightForWidth())
        self.cache_used.setSizePolicy(sizePolicy)
        self.cache_used.setText("cache_used")

        self.active_download_layout.addWidget(self.cache_used, 2, 1, 1, 1)

        self.dl_speed_label = QLabel(DownloadWidget)
        self.dl_speed_label.setObjectName("dl_speed_label")
        self.dl_speed_label.setFont(font1)
        self.dl_speed_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.active_download_layout.addWidget(self.dl_speed_label, 1, 2, 1, 1)

        self.downloaded_label = QLabel(DownloadWidget)
        self.downloaded_label.setObjectName("downloaded_label")
        self.downloaded_label.setFont(font1)
        self.downloaded_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.active_download_layout.addWidget(self.downloaded_label, 2, 2, 1, 1)

        self.dl_speed = QLabel(DownloadWidget)
        self.dl_speed.setObjectName("dl_speed")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dl_speed.sizePolicy().hasHeightForWidth())
        self.dl_speed.setSizePolicy(sizePolicy1)
        self.dl_speed.setText("dl_speed")

        self.active_download_layout.addWidget(self.dl_speed, 1, 3, 1, 1)

        self.time_left_label = QLabel(DownloadWidget)
        self.time_left_label.setObjectName("time_left_label")
        self.time_left_label.setFont(font1)
        self.time_left_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.active_download_layout.addWidget(self.time_left_label, 1, 0, 1, 1)

        self.downloaded = QLabel(DownloadWidget)
        self.downloaded.setObjectName("downloaded")
        sizePolicy1.setHeightForWidth(self.downloaded.sizePolicy().hasHeightForWidth())
        self.downloaded.setSizePolicy(sizePolicy1)
        self.downloaded.setText("downloaded")

        self.active_download_layout.addWidget(self.downloaded, 2, 3, 1, 1)

        self.time_left = QLabel(DownloadWidget)
        self.time_left.setObjectName("time_left")
        sizePolicy.setHeightForWidth(self.time_left.sizePolicy().hasHeightForWidth())
        self.time_left.setSizePolicy(sizePolicy)
        self.time_left.setText("time_left")

        self.active_download_layout.addWidget(self.time_left, 1, 1, 1, 1)

        self.cache_used_label = QLabel(DownloadWidget)
        self.cache_used_label.setObjectName("cache_used_label")
        self.cache_used_label.setFont(font1)
        self.cache_used_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.active_download_layout.addWidget(self.cache_used_label, 2, 0, 1, 1)

        self.progress_bar = QProgressBar(DownloadWidget)
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setValue(0)

        self.active_download_layout.addWidget(self.progress_bar, 3, 0, 1, 4)

        self.kill_button = QPushButton(DownloadWidget)
        self.kill_button.setObjectName("kill_button")

        self.active_download_layout.addWidget(self.kill_button, 3, 4, 1, 1)

        self.active_download_layout.setColumnStretch(1, 1)
        self.active_download_layout.setColumnStretch(3, 1)

        self.retranslateUi(DownloadWidget)
    # setupUi

    def retranslateUi(self, DownloadWidget):
        self.dl_name_label.setText(QCoreApplication.translate("DownloadWidget", "Current download:", None))
        self.dl_speed_label.setText(QCoreApplication.translate("DownloadWidget", "Download speed:", None))
        self.downloaded_label.setText(QCoreApplication.translate("DownloadWidget", "Downloaded:", None))
        self.time_left_label.setText(QCoreApplication.translate("DownloadWidget", "Time left:", None))
        self.cache_used_label.setText(QCoreApplication.translate("DownloadWidget", "Cache size:", None))
        self.kill_button.setText(QCoreApplication.translate("DownloadWidget", "Stop Download", None))
    # retranslateUi


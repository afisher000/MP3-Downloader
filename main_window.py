# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1063, 705)
        self.scroll_area = QtWidgets.QScrollArea(Form)
        self.scroll_area.setGeometry(QtCore.QRect(20, 90, 761, 581))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area.sizePolicy().hasHeightForWidth())
        self.scroll_area.setSizePolicy(sizePolicy)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("scroll_area")
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setGeometry(QtCore.QRect(0, 0, 759, 579))
        self.scroll_widget.setObjectName("scroll_widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scroll_widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.songs_grid = QtWidgets.QGridLayout()
        self.songs_grid.setObjectName("songs_grid")
        self.verticalLayout.addLayout(self.songs_grid)
        self.scroll_area.setWidget(self.scroll_widget)
        self.search_button = QtWidgets.QPushButton(Form)
        self.search_button.setGeometry(QtCore.QRect(170, 50, 101, 31))
        self.search_button.setObjectName("search_button")
        self.download_button = QtWidgets.QPushButton(Form)
        self.download_button.setGeometry(QtCore.QRect(790, 50, 241, 31))
        self.download_button.setObjectName("download_button")
        self.add_songs_button = QtWidgets.QPushButton(Form)
        self.add_songs_button.setGeometry(QtCore.QRect(550, 50, 101, 31))
        self.add_songs_button.setObjectName("add_songs_button")
        self.clear_queue_button = QtWidgets.QPushButton(Form)
        self.clear_queue_button.setGeometry(QtCore.QRect(670, 50, 101, 31))
        self.clear_queue_button.setObjectName("clear_queue_button")
        self.queue_scroll = QtWidgets.QScrollArea(Form)
        self.queue_scroll.setGeometry(QtCore.QRect(790, 90, 261, 581))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.queue_scroll.sizePolicy().hasHeightForWidth())
        self.queue_scroll.setSizePolicy(sizePolicy)
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.queue_scroll.setObjectName("queue_scroll")
        self.queue_widget = QtWidgets.QWidget()
        self.queue_widget.setGeometry(QtCore.QRect(0, 0, 259, 579))
        self.queue_widget.setObjectName("queue_widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.queue_widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.queue_list = QtWidgets.QVBoxLayout()
        self.queue_list.setObjectName("queue_list")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.queue_list.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.queue_list)
        self.queue_scroll.setWidget(self.queue_widget)
        self.search_text = QtWidgets.QLineEdit(Form)
        self.search_text.setGeometry(QtCore.QRect(20, 49, 131, 31))
        self.search_text.setObjectName("search_text")
        self.progressbar = QtWidgets.QProgressBar(Form)
        self.progressbar.setGeometry(QtCore.QRect(290, 52, 111, 31))
        self.progressbar.setProperty("value", 24)
        self.progressbar.setObjectName("progressbar")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.search_button.setText(_translate("Form", "Search Artist"))
        self.download_button.setText(_translate("Form", "Download"))
        self.add_songs_button.setText(_translate("Form", "Add Songs"))
        self.clear_queue_button.setText(_translate("Form", "Clear Queue"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

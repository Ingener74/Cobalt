# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'res/selectrecord.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_WidgetSelectRecord(object):
    def setupUi(self, WidgetSelectRecord):
        WidgetSelectRecord.setObjectName("WidgetSelectRecord")
        WidgetSelectRecord.resize(274, 241)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/main/main.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        WidgetSelectRecord.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(WidgetSelectRecord)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listWidgetSelect = QtWidgets.QListWidget(WidgetSelectRecord)
        self.listWidgetSelect.setObjectName("listWidgetSelect")
        self.verticalLayout.addWidget(self.listWidgetSelect)
        self.pushButtonStart = QtWidgets.QPushButton(WidgetSelectRecord)
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.verticalLayout.addWidget(self.pushButtonStart)

        self.retranslateUi(WidgetSelectRecord)
        QtCore.QMetaObject.connectSlotsByName(WidgetSelectRecord)

    def retranslateUi(self, WidgetSelectRecord):
        _translate = QtCore.QCoreApplication.translate
        WidgetSelectRecord.setWindowTitle(_translate("WidgetSelectRecord", "Выбери запись"))
        self.pushButtonStart.setText(_translate("WidgetSelectRecord", "Старт"))

import resources_rc

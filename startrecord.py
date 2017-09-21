# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'res/startrecord.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_WidgetStartRecord(object):
    def setupUi(self, WidgetStartRecord):
        WidgetStartRecord.setObjectName("WidgetStartRecord")
        WidgetStartRecord.resize(274, 272)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/main/main.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        WidgetStartRecord.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(WidgetStartRecord)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lineEditName = QtWidgets.QLineEdit(WidgetStartRecord)
        self.lineEditName.setObjectName("lineEditName")
        self.verticalLayout.addWidget(self.lineEditName)
        self.textEditDescription = QtWidgets.QTextEdit(WidgetStartRecord)
        self.textEditDescription.setObjectName("textEditDescription")
        self.verticalLayout.addWidget(self.textEditDescription)
        self.pushButtonStart = QtWidgets.QPushButton(WidgetStartRecord)
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.verticalLayout.addWidget(self.pushButtonStart)

        self.retranslateUi(WidgetStartRecord)
        QtCore.QMetaObject.connectSlotsByName(WidgetStartRecord)

    def retranslateUi(self, WidgetStartRecord):
        _translate = QtCore.QCoreApplication.translate
        WidgetStartRecord.setWindowTitle(_translate("WidgetStartRecord", "Начать запись"))
        self.lineEditName.setPlaceholderText(_translate("WidgetStartRecord", "Введите название записи"))
        self.textEditDescription.setPlaceholderText(_translate("WidgetStartRecord", "Здесь вы можете кратко описать запись"))
        self.pushButtonStart.setText(_translate("WidgetStartRecord", "Начать"))

import resources_rc

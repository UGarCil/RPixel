# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_V1.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

from PyQt5 import QtCore, QtGui, QtWidgets
from constants import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1530, 670)
        MainWindow.setStyleSheet("color:white;background-color:rgb(30,30,30);")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setMinimumSize(QtCore.QSize(720, 480))
        self.label.setMaximumSize(QtCore.QSize(720, 480))
        self.label.setStyleSheet("background-color:rgb(50,50,50);")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 1, 1, 1)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 1, 1, 1, 1)
        self.widget_2 = QtWidgets.QWidget(self.centralwidget)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.widget_3 = QtWidgets.QWidget(self.widget_2)
        self.widget_3.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_3.setObjectName("widget_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.widget_3)
        self.label_3.setMaximumSize(QtCore.QSize(300, 16777215))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.number_frames_spinbox = QtWidgets.QSpinBox(self.widget_3)
        self.number_frames_spinbox.setMaximumSize(QtCore.QSize(300, 16777215))
        self.number_frames_spinbox.setObjectName("number_frames_spinbox")
        self.number_frames_spinbox.setMinimum(2)
        self.number_frames_spinbox.setMaximum(20)
        self.number_frames_spinbox.setValue(10)
        self.verticalLayout_2.addWidget(self.number_frames_spinbox)
        self.horizontalLayout_2.addWidget(self.widget_3)
        self.widget = QtWidgets.QWidget(self.widget_2)
        self.widget.setMaximumSize(QtCore.QSize(300, 100))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setMaximumSize(QtCore.QSize(300, 16777215))
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.waitingTime_spinbox = QtWidgets.QDoubleSpinBox(self.widget)
        self.waitingTime_spinbox.setObjectName("doubleSpinBox")
        self.verticalLayout.addWidget(self.waitingTime_spinbox)
        self.horizontalLayout_2.addWidget(self.widget)
        self.gridLayout.addWidget(self.widget_2, 0, 1, 1, 1)
        self.widget_5 = QtWidgets.QWidget(self.centralwidget)
        self.widget_5.setMaximumSize(QtCore.QSize(450, 16777215))
        self.widget_5.setStyleSheet("")
        self.widget_5.setObjectName("widget_5")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget_5)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.widget_6 = QtWidgets.QWidget(self.widget_5)
        self.widget_6.setMaximumSize(QtCore.QSize(16777215, 100))
        self.widget_6.setObjectName("widget_6")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.button_openFolder = QtWidgets.QPushButton(self.widget_6)
        self.button_openFolder.setMinimumSize(QtCore.QSize(60, 60))
        self.button_openFolder.setMaximumSize(QtCore.QSize(60, 60))
        self.button_openFolder.setStyleSheet("background-color:rgb(60,60,60);")
        self.button_openFolder.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/0.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button_openFolder.setIcon(icon)
        self.button_openFolder.setIconSize(QtCore.QSize(40, 40))
        self.button_openFolder.setObjectName("button_openFolder")
        self.horizontalLayout_4.addWidget(self.button_openFolder)
        self.button_SingleShot = QtWidgets.QPushButton(self.widget_6)
        self.button_SingleShot.setMinimumSize(QtCore.QSize(60, 60))
        self.button_SingleShot.setMaximumSize(QtCore.QSize(60, 60))
        self.button_SingleShot.setStyleSheet("background-color:rgb(60,60,60);")
        self.button_SingleShot.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button_SingleShot.setIcon(icon1)
        self.button_SingleShot.setIconSize(QtCore.QSize(40, 40))
        self.button_SingleShot.setObjectName("button_SingleShot")
        self.horizontalLayout_4.addWidget(self.button_SingleShot)
        self.button_timelapse = QtWidgets.QPushButton(self.widget_6)
        self.button_timelapse.setMinimumSize(QtCore.QSize(60, 60))
        self.button_timelapse.setMaximumSize(QtCore.QSize(60, 60))
        self.button_timelapse.setStyleSheet("background-color:rgb(60,60,60);")
        self.button_timelapse.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("icons/1.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button_timelapse.setIcon(icon2)
        self.button_timelapse.setIconSize(QtCore.QSize(40, 40))
        self.button_timelapse.setObjectName("pushButton")
        self.horizontalLayout_4.addWidget(self.button_timelapse)
        self.verticalLayout_3.addWidget(self.widget_6)
        self.widget_4 = QtWidgets.QWidget(self.widget_5)
        self.widget_4.setMinimumSize(QtCore.QSize(400, 0))
        self.widget_4.setMaximumSize(QtCore.QSize(400, 100))
        self.widget_4.setStyleSheet("background-color:rgb(45,45,45);")
        self.widget_4.setObjectName("widget_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget_4)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_4 = QtWidgets.QLabel(self.widget_4)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.prefix_lineEdit = QtWidgets.QLineEdit(self.widget_4)
        self.prefix_lineEdit.setMaximumSize(QtCore.QSize(300, 16777215))
        self.prefix_lineEdit.setObjectName("prefix_lineEdit")
        self.horizontalLayout_3.addWidget(self.prefix_lineEdit)
        self.verticalLayout_3.addWidget(self.widget_4, 0, QtCore.Qt.AlignHCenter)
        self.gridLayout.addWidget(self.widget_5, 2, 0, 1, 1)
        ####
        self.buttonStatus = QtWidgets.QPushButton(self.centralwidget)
        self.buttonStatus.setMinimumSize(QtCore.QSize(60, 60))
        self.buttonStatus.setMaximumSize(QtCore.QSize(60, 60))
        self.buttonStatus.setStyleSheet("background-color:rgb(60,60,60);")
        self.buttonStatus.setText("")
        self.icon3 = QtGui.QIcon()
        self.icon3.addPixmap(QtGui.QPixmap("icons/3.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon4 = QtGui.QIcon()
        self.icon4.addPixmap(QtGui.QPixmap("icons/4.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.buttonStatus.setIcon(self.icon3)
        self.buttonStatus.setIconSize(QtCore.QSize(50, 50))
        self.buttonStatus.setObjectName("buttonStatus")
        self.gridLayout.addWidget(self.buttonStatus, 0, 0, 1, 1, QtCore.Qt.AlignHCenter)
        ####
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1530, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuAbout = QtWidgets.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew = QtWidgets.QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSet_prefix = QtWidgets.QAction(MainWindow)
        self.actionSet_prefix.setObjectName("actionSet_prefix")
        self.actionGitHub = QtWidgets.QAction(MainWindow)
        self.actionGitHub.setObjectName("actionGitHub")
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuEdit.addAction(self.actionSet_prefix)
        self.menuAbout.addAction(self.actionGitHub)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        # self.label.setText(_translate("MainWindow", "Camera Feed"))
        self.label_3.setText(_translate("MainWindow", "No. Frames"))
        self.label_2.setText(_translate("MainWindow", "Seconds in between"))
        self.label_4.setText(_translate("MainWindow", "Prefix"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuAbout.setTitle(_translate("MainWindow", "About"))
        self.actionNew.setText(_translate("MainWindow", "New.."))
        self.actionOpen.setText(_translate("MainWindow", "Open..."))
        self.actionSet_prefix.setText(_translate("MainWindow", "Set_prefix"))
        self.actionGitHub.setText(_translate("MainWindow", "GitHub"))


# DD. DISPLAY_WIDGET
# displayWidget = WebcamWidget(QLabel)
# interp. a child class optimized for event controlling
class WebcamWidget(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def enterEvent(self, event):
        """Hide the cursor when the mouse enters the widget."""
        self.setCursor(Qt.BlankCursor)
        cursor_settings["in_display"] = True

    def leaveEvent(self, event):
        """Restore the cursor when the mouse leaves the widget."""
        self.setCursor(Qt.ArrowCursor)
        cursor_settings["in_display"] = False

if __name__ == "__main__":
    print("call the script main.py instead...")

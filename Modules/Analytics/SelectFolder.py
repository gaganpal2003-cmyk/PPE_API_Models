# -*- coding: utf-8 -*-
import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog


class Ui_NewCameraDlg(object):
    def setupUi(self, NewCameraDlg):
        NewCameraDlg.setObjectName("NewCameraDlg")
        NewCameraDlg.resize(500, 150)

        # Keep reference of the QDialog
        self.dialog = NewCameraDlg

        # Main vertical layout
        self.mainLayout = QtWidgets.QVBoxLayout(NewCameraDlg)

        # --------- First row (Folder label + input + browse) ---------
        folderLayout = QtWidgets.QHBoxLayout()
        self.current_dir = os.getcwd()
        self.icon_path = f"{self.current_dir}\icon"
        self.label_2 = QtWidgets.QLabel("Folder:")
        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_2.setFont(font)

        self.txtPlatUrl = QtWidgets.QLineEdit()
        self.txtPlatUrl.setMinimumWidth(250)
        self.txtPlatUrl.setMinimumHeight(30)

        self.btnbrowse = QtWidgets.QPushButton()
        self.btnbrowse.setFixedSize(40, 28)
        self.btnbrowse.clicked.connect(self.pick_new)

        # Add to horizontal layout
        folderLayout.addWidget(self.label_2)
        folderLayout.addWidget(self.txtPlatUrl)
        folderLayout.addWidget(self.btnbrowse)

        # --------- Second row (buttons) ---------
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setSpacing(20)
        buttonLayout.setAlignment(QtCore.Qt.AlignCenter)

        self.btnReset = QtWidgets.QPushButton("&Reset")
        self.btnReset.setFixedSize(75, 40)
        self.btnAdd = QtWidgets.QPushButton("&Ok")
        self.btnAdd.setFixedSize(75, 40)
        self.btnCancel = QtWidgets.QPushButton("&Cancel")
        self.btnCancel.setFixedSize(75, 40)

        # Button actions
        self.btnReset.clicked.connect(self.reset_input)
        self.btnCancel.clicked.connect(self.dialog.reject)   # close dialog without output
        self.btnAdd.clicked.connect(self.accept_and_return)  # close with output

        buttonLayout.addWidget(self.btnReset)
        buttonLayout.addWidget(self.btnAdd)
        buttonLayout.addWidget(self.btnCancel)

        # Add layouts to main layout
        self.mainLayout.addLayout(folderLayout)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addLayout(buttonLayout)

        # Apply stylesheet with custom colors
        NewCameraDlg.setStyleSheet("""
            QLabel {
                color: white;
            }
            QLineEdit {
                color: white;
            }
            QPushButton {
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton#btnReset {
                background-color: #0078d7; /* Blue */
            }
            QPushButton#btnReset:hover {
                background-color: #005a9e;
            }
            QPushButton#btnAdd {
                background-color: #28a745; /* Green */
            }
            QPushButton#btnAdd:hover {
                background-color: #1e7e34;
            }
            QPushButton#btnCancel {
                background-color: #dc3545; /* Red */
            }
            QPushButton#btnCancel:hover {
                background-color: #a71d2a;
            }
        """)

        # Set button object names for styles
        self.btnReset.setObjectName("btnReset")
        self.btnAdd.setObjectName("btnAdd")
        self.btnCancel.setObjectName("btnCancel")

        # Set browse icon
        icon_file = os.path.join(rf"{self.icon_path}\file.png")
        if os.path.exists(icon_file):
            self.btnbrowse.setIcon(QIcon(icon_file))
            self.btnbrowse.setIconSize(QSize(20, 20))

    def pick_new(self):
        folder = QFileDialog.getExistingDirectory(self.dialog, "Select Folder")
        if folder:
            self.txtPlatUrl.setText(folder)

    def reset_input(self):
        self.txtPlatUrl.clear()

    def accept_and_return(self):
        # Get the selected folder
        folder = self.txtPlatUrl.text()
        if folder.strip():
            self.folder = os.path.normpath(folder)
            print("Selected Folder:", self.folder)
        if len(self.folder.strip()) > 1:
            self.dialog.accept()   # close with success

    def getFolderName(self):
        return self.folder
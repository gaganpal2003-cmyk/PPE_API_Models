from tkinter import font

from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtWidgets import QLabel, QPushButton, QTableWidgetItem, QHBoxLayout, QAbstractItemView, QTableWidget, \
    QVBoxLayout, QFrame, QLineEdit, QGridLayout, QWidget, QHeaderView, QDialog, QMessageBox, QTimeEdit, QDateEdit, \
    QSizePolicy, QComboBox


class AnalyticTab(QWidget):
    def __init__(self, main):
        super().__init__()
        self.highlighted_button = None
        self.buttonWidth = 60
        self.buttonHeight = 30
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Graph Data')
        self.isFullScreen()

        self.mainLayout = QHBoxLayout()

        self.buttonLayout = QHBoxLayout()

        self.buttonLayout.setAlignment(Qt.AlignTop)
        self.buttonAndGraphLayout = QVBoxLayout()

        self.graphAndReportLayout = QHBoxLayout()
        self.graphLayout = QHBoxLayout()

        # self.graphAndReportLayout.addLayout(self.graphLayout)

        self.leftButtonLayout = QHBoxLayout()
        self.rightButtonLayout = QHBoxLayout()

        ####
        self.camList = QComboBox()
        self.camList.setFixedSize(120, self.buttonHeight)
        self.cameraSel = QLabel('Select Camera:')
        self.cameraSel.setFixedSize(80, self.buttonHeight)
        self.leftButtonLayout.addWidget(self.cameraSel)
        self.leftButtonLayout.addWidget(self.camList)

        self.today = QPushButton("Today")
        # self.today.setStyleSheet("background-color: #01BDF8; color: black;")
        self.today.clicked.connect(lambda: self.highlight_button(self.today))
        self.today.setFixedSize(self.buttonWidth, self.buttonHeight)
        self.rightButtonLayout.addWidget(self.today)

        self.oneDays = QPushButton("1D")
        self.oneDays.clicked.connect(lambda: self.highlight_button(self.oneDays))
        self.oneDays.setFixedSize(self.buttonWidth, self.buttonHeight)
        self.rightButtonLayout.addWidget(self.oneDays)

        self.sevenDays = QPushButton("7D")
        self.sevenDays.clicked.connect(lambda: self.highlight_button(self.sevenDays))
        self.sevenDays.setFixedSize(self.buttonWidth, self.buttonHeight)
        self.rightButtonLayout.addWidget(self.sevenDays)

        self.oneMonth = QPushButton("1M")
        self.oneMonth.clicked.connect(lambda: self.highlight_button(self.oneMonth))
        self.oneMonth.setFixedSize(self.buttonWidth, self.buttonHeight)
        self.rightButtonLayout.addWidget(self.oneMonth)

        # self.leftButtonLayout.setAlignment(Qt.AlignLeft)
        self.rightButtonLayout.setAlignment(Qt.AlignRight)
        self.buttonLayout.addLayout(self.leftButtonLayout)
        self.buttonLayout.addLayout(self.rightButtonLayout)
        self.reportSecLayout = QVBoxLayout()

        self.bottomFrame = QFrame()
        self.bottomFrame.setFrameStyle(QFrame.Panel | QFrame.Plain)  # Add a border to the frame
        self.bottomFrame.setLineWidth(2)

        self.reportLayout = QGridLayout()
        self.buttonAndGraphLayout.addLayout(self.buttonLayout)
        self.buttonAndGraphLayout.addLayout(self.graphLayout)

        self.reportSecLayout.addLayout(self.reportLayout)
        self.reportSecLayout.addWidget(self.bottomFrame)

        #
        self.mainLayout.addLayout(self.reportSecLayout)
        self.mainLayout.addLayout(self.buttonAndGraphLayout,8)

        self.setLayout(self.mainLayout)

    def highlight_button(self, clicked_button):
        # Reset styles of all buttons
        self.today.setStyleSheet("")
        self.oneDays.setStyleSheet("")
        self.sevenDays.setStyleSheet("")
        self.oneMonth.setStyleSheet("")
        # Highlight the clicked button
        clicked_button.setStyleSheet("background-color: #01BDF8; color: black;")
        self.highlighted_button = clicked_button

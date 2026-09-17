from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QTableWidget, QGridLayout, QVBoxLayout


class Report(QWidget):
    def __init__(self, main):
        super().__init__()
        self.table = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Report Layout')
        self.mainLayout = QHBoxLayout()
        self.isFullScreen()
        self.main_frameLayout = QFrame()

        # self.main_frameLayout.setFixedWidth(900)
        self.mainLayout.setSpacing(0)
        self.table = QTableWidget()
        self.rightLayout = QVBoxLayout()
        self.topFrame = QFrame()
        self.ReportLayout = QGridLayout()
        self.bottomFrame = QFrame()
        self.bottomFrame.setFrameStyle(QFrame.Panel | QFrame.Plain)  # Add a border to the frame
        self.bottomFrame.setLineWidth(2)
        self.rightLayout.addLayout(self.ReportLayout)
        self.rightLayout.addWidget(self.bottomFrame)

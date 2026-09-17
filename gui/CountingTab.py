from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QTableWidget, QGridLayout, QVBoxLayout


class BagsCounting(QWidget):
    def __init__(self, main):
        super().__init__()
        self.table = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Report Layout')
        self.isFullScreen()

        self.mainLayout = QHBoxLayout()
        self.right_frame = QFrame()
        self.right_frame.setFrameStyle(QFrame.Panel | QFrame.Plain)  # Add a border to the frame
        self.right_frame.setLineWidth(2)
        self.left_frame = QFrame()
        self.left_frame.setFrameStyle(QFrame.Panel | QFrame.Plain)  # Add a border to the frame
        self.left_frame.setLineWidth(2)

        self.mainLayout.setSpacing(0)
        self.rightLayout = QVBoxLayout()
        self.right_frame.setLayout(self.rightLayout)

        self.ReportLayout = QGridLayout()

        self.graphLayout = QHBoxLayout()
        self.left_frame.setLayout(self.graphLayout)
        self.table = QTableWidget()
        self.bottomFrame = QFrame()
        self.tableLayout = QHBoxLayout()
        # self.bottomFrame.setLayout(self.tableLayout)
        # self.bottomFrame.setFrameStyle(QFrame.Panel | QFrame.Plain)  # Add a border to the frame
        # self.bottomFrame.setLineWidth(2)
        # self.mainLayout.addLayout(self.graphLayout)
        self.rightLayout.addLayout(self.ReportLayout)
        self.rightLayout.addWidget(self.table)
        self.mainLayout.addWidget(self.left_frame, 80)
        self.mainLayout.addWidget(self.right_frame)
        self.setLayout(self.mainLayout)
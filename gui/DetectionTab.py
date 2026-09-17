from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QTableWidgetItem, QHBoxLayout, QAbstractItemView, QTableWidget, \
    QVBoxLayout, QFrame, QLineEdit, QGridLayout, QWidget, QHeaderView, QDialog, QMessageBox, QTimeEdit, QDateEdit, \
    QSizePolicy, QScrollArea

ROWS = 6
COLS = 10


# class ImageFrame(QFrame):
#     imageClicked = pyqtSignal(int, int)  # Emit row and column information
#
#     def __init__(self, row, col):
#         super().__init__()
#         self.image_label = None
#         self.row = row
#         self.col = col
#         self.runningSlide()
#         # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#
#     def runningSlide(self):
#         self.image_label = QLabel()
#         self.image_label.setStyleSheet("border: none;")
#         # self.image_label.setAlignment(Qt.AlignCenter)
#         # self.image_label.setFixedSize(120, 120)
#         # self.image_label.setStyleSheet("border: 1px solid white;")
#         layout = QVBoxLayout()
#         layout.setAlignment(Qt.AlignCenter)
#         layout.addWidget(self.image_label)
#
#         self.setLayout(layout)
#
#     def mousePressEvent(self, event):
#         print("--------------------")
#         print("I clicked the mouse press event....")
#         print(f"row:- {self.row}\ncol:- {self.col}")
#         print("--------------------")
#         self.imageClicked.emit(self.row, self.col)
#
#     def clear_image(self):
#         self.image_label.clear()


class DetectionTabForm(QWidget):
    def __init__(self, main):
        super().__init__()
        self.SearchBoxLayout = None
        self.ImageFrameLayout = None
        self.RightFrame = None
        self.LeftFrame = None
        self.mainLayout = None
        self.initUI()
        # self.displayImageIntoFrame()

    # def displayImageIntoFrame(self):
    #     self.RightFrame.setStyleSheet("QFrame {background-color: #808080;"
    #                                   "border-width: 1;"
    #                                   "border-radius: 3;"
    #                                   "border-style: solid;}"
    #                                   )
    #     self.vertical_layout = QVBoxLayout()
    #     for row in range(ROWS):
    #         horizontal_layout = QHBoxLayout()
    #         horizontal_layout.setSpacing(0)
    #         for col in range(COLS):
    #             image_frame = ImageFrame(row, col)  # Pass row and col information
    #             horizontal_layout.addWidget(image_frame)
    #         self.vertical_layout.addLayout(horizontal_layout)
    #
    #     self.RightFrame.setLayout(self.vertical_layout)

    def initUI(self):
        self.setWindowTitle('Datails')
        self.isFullScreen()
        self.mainLayout = QHBoxLayout()
        self.LeftFrame = QFrame()
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.RightFrame = QFrame()
        self.scroll_area.setWidget(self.RightFrame)
        self.RightFrame.setStyleSheet("QFrame {background-color: #808080;"
                                                    "border-width: 1;"
                                                    "border-radius: 3;"
                                                    "border-style: solid;}"
                                                    )
        self.RightFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.SearchBoxLayout = QGridLayout()
        self.LeftFrame.setLayout(self.SearchBoxLayout)

        self.mainLayout.addWidget(self.LeftFrame, 2)
        self.mainLayout.addWidget(self.scroll_area, 8)
        self.setLayout(self.mainLayout)

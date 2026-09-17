import os

from PyQt5.QtCore import Qt, QSize, QObject
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QFrame, QSizePolicy, QLabel, QHBoxLayout, QVBoxLayout


class ImageFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 110)
        self.image_label.setStyleSheet("border: 1px solid white;")
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class CameraDetectPopup(QFrame):
    def __init__(self, icon_path, objName):
        super().__init__()
        # self.setFixedSize(260, 110)
        self.setFixedWidth(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_pth = icon_path
        self.objName = objName
        border_radius = 15
        text_color = "white"
        self.final_frame = QFrame()

        self.setStyleSheet(f"""
            border: white;
            border-radius: {border_radius}px;
            border: 1px solid white;  /* Border color */
            color: {text_color};
            ;
        """)
        self.info_label = QLabel(f"Camera 1")
        # self.info_label.setFixedSize(70, 70)
        self.info_label.setStyleSheet("""
                    QLabel {
                        font-weight: bold;
                        font-size: 15px;
                        color: white;

                        border: none;
                    }
                """)

        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft)
        self.image_label = QLabel()
        movie = QMovie(self.icon_pth)
        movie.setScaledSize(QSize(120, 80))
        self.image_label.setMovie(movie)
        movie.start()
        self.image_label.setStyleSheet("background: transparent; border: none; color: black;")
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)


class ObjectCountPopup(QFrame):
    def __init__(self, icon_path, objName):
        super().__init__()
        # self.setFixedSize(260, 110)
        self.setFixedWidth(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_pth = icon_path
        self.objName = objName
        border_radius = 15
        text_color = "white"
        self.final_frame = QFrame()

        self.setStyleSheet(f"""
            border: white;
            border-radius: {border_radius}px;
            border: 1px solid white;  /* Border color */
            color: {text_color};
            ;
        """)
        self.info_label = QLabel(f"0")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFixedSize(70, 70)
        self.info_label.setStyleSheet("""
                    QLabel {
                        font-weight: bold;
                        font-size: 12px;
                        color: white;
                        background-color: #007bff;
                        border-radius: 35px;
                        border: 2px solid #ced4da;
                    }
                """)

        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft)
        self.image_label = QLabel()
        movie = QMovie(self.icon_pth)
        movie.setScaledSize(QSize(120, 80))
        self.image_label.setMovie(movie)
        movie.start()
        self.image_label.setStyleSheet("background: transparent; border: none; color: black;")

        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)


class DetectFrameRight(QObject):
    def __init__(self, configData, parent=None):
        super(DetectFrameRight, self).__init__(parent)
        self.configData = configData
        self.defaultGif = f"{str(self.configData.get_default_gif())}.png"
        print("default gif ramesh:- ", self.defaultGif)
        self.mainWdgt = parent
        self.set_right_frame()

    def set_right_frame(self):
        popupLayout = QVBoxLayout()
        obj = "Hello"
        self.info_label = QLabel(f"1000\n{obj}")
        self.info_label.setStyleSheet("font-size: 15px;")
        self.image_label = QLabel()
        self.main_popup_layout = QVBoxLayout()

        self.layout = QHBoxLayout()
        self.layout_2 = QHBoxLayout()
        self.main_popup_layout.addLayout(self.layout)
        self.main_popup_layout.addLayout(self.layout_2)
        self.image_label = QLabel()
        popupIconPath = os.getcwd()
        objectGIFPath = popupIconPath + fr"\popupIcons\{self.defaultGif}"
        signPath = popupIconPath + r"\popupIcons\right_sign.png"
        self.layout.addWidget(ObjectCountPopup(objectGIFPath, 'ppe'))
        self.layout_2.addWidget(CameraDetectPopup(signPath, 'Camera 1'))

        detectLayoutRight = QVBoxLayout()
        detectLayoutRight.setSpacing(0)
        for i in range(0, 6 - 1, 2):  # Iterate through pairs of images
            image_pair_layout = QHBoxLayout()  # Create a horizontal layout for each pair
            image_pair_layout.setSpacing(0)
            for j in range(2):
                image_label = ImageFrame()
                image_pair_layout.addWidget(image_label)
            detectLayoutRight.addLayout(image_pair_layout)
        popupLayout.addLayout(self.main_popup_layout)
        popupLayout.addLayout(detectLayoutRight)
        self.mainWdgt.FrmRecogt.setLayout(popupLayout)

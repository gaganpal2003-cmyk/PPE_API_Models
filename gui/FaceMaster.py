import os
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets, QtCore
from gui.DetectionTab import *
# from gui.DetectTab import *
from gui.AnalyticsTab import *
from gui.ReportTab import *
from gui.CountingTab import *


class AlignLeftDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter


class camButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 30)

        # self.setStyleSheet("QPushButton"
        #                    "{"
        #                    "background-color : #313131; border: 2px; border-style: outset;"
        #                    "}"
        #                    )
        icon_size = QSize(18, 15)
        self.setIconSize(icon_size)


class TabWindow(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWindow, self).__init__(parent)
        self.drawing = False
        self.newCoordinate = False
        self.lines = []
        self.current_tab = None
        self.initTabs()


    def initTabs(self):
        self.livetab = QtWidgets.QWidget()
        self.livetab.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.livetab.setObjectName("livetab")
        self.current_tab = "livetab"
        icon_path = os.getcwd()
        icon_path += r"\ImageIcons"
        self.live = self.addTab(self.livetab, "Live")
        self.setTabIcon(self.live, QIcon(f"{icon_path}\live.png"))
        self.tabBar().setStyleSheet(
            "QTabBar::tab { height: 30px; font-size: 17px; color: rgb(135, 206, 250);}")

        ####
        # self.Detectiontab = DetectionTabForm(QWidget)  # QtWidgets.QWidget()
        # self.Detectiontab.setContextMenuPolicy(Qt.DefaultContextMenu)
        # self.Detectiontab.setObjectName("Detectiontab")
        # self.Master = self.addTab(self.Detectiontab, "Detection")
        #
        #
        self.Analyticstab = AnalyticTab(QWidget)  # QtWidgets.QWidget()
        self.Analyticstab.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.Analyticstab.setObjectName("Analyticstab")
        self.Master = self.addTab(self.Analyticstab, "Analytics")
        # #####
        #
        # ###
        # self.CountingTab = BagsCounting(QWidget)
        # self.CountingTab.setContextMenuPolicy(Qt.DefaultContextMenu)
        # self.CountingTab.setObjectName("CountingTab")
        # self.Counting = self.addTab(self.CountingTab, "Counting")
        # # self.setTabIcon(self.Report, QIcon(fr"{icon_path}\report.png"))
        # ###
        # ###
        # self.ReportTab = Report(QWidget)
        # self.ReportTab.setContextMenuPolicy(Qt.DefaultContextMenu)
        # self.ReportTab.setObjectName("ReportTab")
        # self.Report = self.addTab(self.ReportTab, "Report")
        # # self.setTabIcon(self.Report, QIcon(fr"{icon_path}\report.png"))
        # ##
        self.currentChanged.connect(self.on_tab_changed)

        self.MainLayout = QtWidgets.QVBoxLayout(self.livetab)
        self.SubLayout = QtWidgets.QHBoxLayout()

        self.MainLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.MainLayout.setContentsMargins(1, 0, 0, 0)
        self.MainLayout.setObjectName("horizontalLayout")
        self.MainLayout.setSpacing(0)

        self.FrmLive = QtWidgets.QFrame()
        spLeft = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        spLeft.setHorizontalStretch(1)
        self.FrmLive.setSizePolicy(spLeft)

        self.FrmLive.setFrameShape(QtWidgets.QFrame.Box)
        self.FrmLive.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrmLive.setObjectName("FrmLive")

        self.videoPlay = QWidget()
        ######
        # #
        ######
        # self.videoPlay.setLayout()
        # self.liveFrameLayout = QVBoxLayout()

        # self.videoPlay.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.videoPlay.setAlignment(Qt.AlignCenter)
        # self.videoPlay.setStyleSheet("QLabel {background-color: #313131;}")
        # self.videoPlay_Widh = 400
        # self.videoPlay_Height = 300
        self.LineClearLayout = QHBoxLayout()
        spRight = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        spRight.setHorizontalStretch(2)

        self.FrmRecogt = QtWidgets.QFrame()
        self.FrmRecogt.setSizePolicy(spRight)
        self.FrmRecogt.setFrameShape(QtWidgets.QFrame.Box)
        self.FrmRecogt.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrmRecogt.setObjectName("FrmRecogt")

        self.FrmDetect = QtWidgets.QFrame()
        self.FrmDetect.setFrameShape(QtWidgets.QFrame.Box)
        self.FrmDetect.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrmDetect.setObjectName("FrmDetect")

        self.CameraQFrame = QtWidgets.QFrame()
        self.CameraQFrame.setFrameShape(QtWidgets.QFrame.Box)
        self.CameraQFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.CameraQFrame.setObjectName("CameraQFrame")

        self.CameraLayout = QtWidgets.QVBoxLayout()
        self.CameraQFrame.setLayout(self.CameraLayout)
        self.CameraLayout.setSpacing(1)

        self.camList = QtWidgets.QComboBox()
        self.camList.setObjectName("camList")
        self.camList.setFixedSize(150, 40)
        self.CameraConf = camButton("Camera")

        self.CameraConf.setStyleSheet("QPushButton"
                                    "{"
                                    "background-color : #72C9FF; border: 2px; color: black; border-style: outset;"
                                    "}"
                                    )
        self.CameraLayout.setAlignment(self.CameraConf, Qt.AlignCenter)
        self.LineClearLayout.addWidget(self.CameraConf)
        self.drawLine = camButton("Draw Box")

        self.drawLine.setStyleSheet("QPushButton"
                                    "{"
                                    "background-color : #64A651; border: 2px; color: black; border-style: outset;"
                                    "}"
                                    )
        self.LineClearLayout.addWidget(self.drawLine)


        # self.CameraLayout.addWidget(self.CameraConf)
        # self.CameraLayout.addWidget(self.CameraConf, alignment=Qt.AlignCenter)
        self.CameraLayout.addLayout(self.LineClearLayout)

        self.CameraLayout.addWidget(self.camList)
        self.CameraLayout.addStretch()

        self.DetectLayout = QtWidgets.QHBoxLayout()
        self.DetectLayout.setSpacing(0)

        self.DetectLayout.addWidget(self.CameraQFrame, 40)
        self.DetectLayout.addWidget(self.FrmDetect, 60)

        self.SubLayout.setSpacing(0)


        self.SubLayout.addWidget(self.videoPlay, 90)
        self.SubLayout.addWidget(self.FrmRecogt, 10)

        self.MainLayout.addLayout(self.SubLayout, 80)
        self.MainLayout.addLayout(self.DetectLayout, 20)

    def on_tab_changed(self, index):
        current_tab = self.currentWidget()
        self.current_tab = current_tab.objectName()

    def resizeEvent(self, event):
        self.tabBar().setFixedWidth(200)
        super(TabWindow, self).resizeEvent(event)

    def changeEvent(self, event):
        print("The application is minimized.")

    def updateTabSize(self):
        return 450

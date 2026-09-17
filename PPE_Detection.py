import sys
import qdarkstyle
from PyQt5.QtGui import QFont

from Modules.DbManager import Databasemgr
from Modules.Live.cameraMgr import *
# from Modules.Detection.DetectionData import *
from Modules.Analytics.AnalyticsData import *
# from Modules.Report.ReportData import *
# from Modules.Counting.CountingData import *
from Modules.Live.configRead import *
from gui.FaceMaster import *
from Modules.DbManagerMysql import *
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer


class DrawRectangle(QWidget):
    def __init__(self, cameraConf, dbr, parent=None):
        super(DrawRectangle, self).__init__(parent)
        self.dbr = dbr
        self.cameraConf = cameraConf
        self.mainWidget = parent

        if self.cameraConf is not None:
            frame = self.cameraConf.getCurrentFrame()
            if frame is not None:
                cv2.namedWindow("SelectROI", flags=cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
                cv2.imshow("SelectROI", frame)
                showCrosshair = False
                fromCenter = False
                self.ROIs = cv2.selectROIs("SelectROI", frame, showCrosshair, fromCenter)
                xy = (self.ROIs[0][0], self.ROIs[0][1])
                x1y1 = (self.ROIs[0][2], self.ROIs[0][3])
                currentCamera = self.mainWidget.camList.currentText()
                # update_camera = f"""
                #                                         UPDATE camera_frame_coordinates
                #                                        SET status = 1, xy = '{xy}', x1y1 = '{x1y1}'
                #                                         WHERE cameName = '{currentCamera}';
                #                                      """
                # self.dbr.execute(update_camera)
                # currentCamera = self.mainWidget.camList.currentText()
                existing = self.dbr.select(f"SELECT id FROM camera_frame_coordinates WHERE cameName='{currentCamera}'")
                if existing:
                    update_camera = f"""
                        UPDATE camera_frame_coordinates
                        SET status = 1, xy = '{xy}', x1y1 = '{x1y1}'
                        WHERE cameName = '{currentCamera}';
                    """
                else:
                    update_camera = f"""
                        INSERT INTO camera_frame_coordinates (cameName, xy, x1y1, status)
                        VALUES ('{currentCamera}', '{xy}', '{x1y1}', 1);
                    """

                self.dbr.execute(update_camera)

                self.mainWidget.newCoordinate = True

            else:
                print("Frame is empty")
            cv2.destroyWindow("SelectROI")

    def mouseDoubleClickEvent(self, event):
        event.accept()

class EmojiFrame(QFrame):
    def __init__(self, image_path):
        super().__init__()
        self.setFixedSize(120, 120)
        self.image_label = QLabel()
        movie = QMovie(image_path)
        movie.setScaledSize(QSize(120, 120))
        self.image_label.setMovie(movie)
        movie.start()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.image_label)
        self.setLayout(layout)


class ImageLabelWidget(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__()
        self.mainWidget = parent
        self.setWindowTitle("PyQt Image and Label GUI")
        self.setStyleSheet("background-color: #19232D;")

        # image_frame = EmojiFrame(image_path)
        image_label = QLabel()
        movie = QMovie(image_path)
        movie.setScaledSize(QSize(120, 120))
        image_label.setMovie(movie)
        # image_label.setAlignment(Qt.AlignLeft)
        movie.start()

        label = QLabel(f"Click the camera button \nbelow to start live \nstream or video!")
        label.setStyleSheet("color: white; border: none;")

        font = QFont()
        font.setPointSize(15)
        label.setFont(font)
        # label.setAlignment(Qt.AlignBottom)

        vertical_layout = QVBoxLayout()
        vertical_layout.setAlignment(Qt.AlignBottom)
        vertical_layout.addWidget(label)
        vertical_layout.addWidget(image_label)

        # self.setLayout(vertical_layout)
        self.mainWidget.videoPlay.setLayout(vertical_layout)


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


class FaceRecogApp(QtWidgets.QMainWindow):
    def __init__(self):
        try:
            super(FaceRecogApp, self).__init__()
            self.mainWidget = TabWindow()
            # self.mainWidget.setStyleSheet('background-color: rgba(148, 176, 212, 1);')
            self.setCentralWidget(self.mainWidget)
            self.mainWidget.drawLine.clicked.connect(self.drawRectangleInFrame)
            self.setWindowTitle("PPE Detection")
            self.mainWidget.CameraConf.clicked.connect(self.configCamera)
            # self.configCamera()
            self.Config = ConfigData(os.getcwd())
            # self.dbMysqlMgr = Databasemgr(self.Config.get_db_path())
            self.dbMysqlMgr = DatabaseMysqlmgr(self.Config.get_db_name())
            self.dbMysqlMgr.execute("""
                CREATE TABLE IF NOT EXISTS camera_frame_coordinates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cameName VARCHAR(255) NOT NULL,
                    xy TEXT,
                    x1y1 TEXT,
                    status INT DEFAULT 1
                );
            """)
            # self.reg = DetectionForm(self.dbMysqlMgr, self.mainWidget.Detectiontab)
            # # self.reg = DetectForm(self.dbMysqlMgr, self.mainWidget.Detecttab)
            self.analytics = AnalyticData(self.dbMysqlMgr, self.mainWidget.Analyticstab, self.mainWidget)
            # self.report = DownloadReport(self.dbMysqlMgr, self.mainWidget.ReportTab, self.mainWidget)
            # self.counting = BagsCountingData(self.dbMysqlMgr, self.mainWidget.CountingTab, self.mainWidget)
            self.cameraList = []
            self.cameraConf = None
            self.display_cam_list()
            # self.display_line_camera_list()
            ob_lst = self.Config.get_object_list()
            self.set_bottom_frame()
            self.userSuggestion()
            # self.set_right_frame()
            self.mainWidget.camList.currentIndexChanged.connect(self.on_camera_changed)
            desktop = QApplication.desktop()
            width = desktop.width()
            height = desktop.height()
            print("width:- ", width)
            print("height:- ", height)
            self.setFixedSize(width - 10, height - 75)
            self.show()
            QTimer.singleShot(200, self.autoStartCamera)

        except Exception as e:
            print(e)
            exit(1)

    def on_camera_changed(self):
        currentCamera = self.mainWidget.camList.currentText()
        if currentCamera and currentCamera != "Select Camera":
            try:
                self.dbMysqlMgr.execute(f"UPDATE camera SET status = 1 WHERE cameName = '{currentCamera}';")
                print(f"[DB] Active camera changed to: {currentCamera} (status set to 1)")
            except Exception as e:
                print(f"[DB Error] updating status for {currentCamera}: {e}")

    def autoStartCamera(self):
        try:
            active_cams = self.dbMysqlMgr.select("select id, cameName, camUrl, location, status from camera where status = 1")
            if not active_cams or len(active_cams) == 0:
                if len(self.cameraList) > 0:
                    first_cam_name = self.cameraList[0][1]
                    try:
                        self.dbMysqlMgr.execute(f"UPDATE camera SET status = 1 WHERE cameName = '{first_cam_name}';")
                        active_cams = self.dbMysqlMgr.select(f"select id, cameName, camUrl, location, status from camera where cameName = '{first_cam_name}'")
                    except Exception as e:
                        print(f"Error activating fallback camera: {e}")

            if active_cams and len(active_cams) > 0:
                selected_cams = [cam[1] for cam in active_cams]
                if self.cameraConf is None:
                    self.cameraConf = CameraMgr(self.dbMysqlMgr, self.cameraList, selected_cams, self.Config, self.mainWidget)
                self.cameraConf.selected_camera = selected_cams
                self.cameraConf.startCamera()
                print(f"Auto-started previously ON camera(s): {selected_cams}. Active camera: {self.mainWidget.camList.currentText()}")
            else:
                print("No camera found in database to auto-start.")
        except Exception as e:
            print(f"Error auto-starting camera: {e}")

    def drawRectangleInFrame(self):
        currentCamera = self.mainWidget.camList.currentText()
        print("Current camera change:- ", currentCamera)
        if self.cameraConf is not None:
            DrawRectangle(self.cameraConf, self.dbMysqlMgr, self.mainWidget)
    def userSuggestion(self):
        popupIconPath = os.getcwd()
        objectGIFPath = popupIconPath + fr"\popupIcons\startCamera.gif"
        widget = ImageLabelWidget(objectGIFPath, self.mainWidget)
        VLayout = QVBoxLayout()
        VLayout.addWidget(widget)

    def set_bottom_frame(self):
        detectLayoutButton = QHBoxLayout()
        for f in range(10):
            image_frame = ImageFrame()
            detectLayoutButton.addWidget(image_frame)
        self.mainWidget.FrmDetect.setLayout(detectLayoutButton)

    def display_cam_list(self):
        self.cameraList.clear()
        data = self.dbMysqlMgr.select("select id, cameName, camUrl, location, status from camera")
        self.mainWidget.camList.clear()
        self.mainWidget.camList.addItem("Select Camera")
        active_idx = -1
        for i, row in enumerate(data):
            self.cameraList.append(row)
            self.mainWidget.camList.addItem(row[1])
            if len(row) > 4 and row[4] == 1 and active_idx == -1:
                active_idx = i + 1
        if active_idx != -1:
            self.mainWidget.camList.setCurrentIndex(active_idx)

    def configCamera(self):
        self.display_cam_list()
        active_cams = [cam[1] for cam in self.cameraList if len(cam) > 4 and cam[4] == 1]
        if self.cameraConf is None:
            self.cameraConf = CameraMgr(self.dbMysqlMgr, self.cameraList, active_cams, self.Config, self.mainWidget)
        else:
            self.cameraConf.cameraList = self.cameraList
            self.cameraConf.selected_camera = active_cams
        if self.cameraConf is not None:
            self.cameraConf.display_cam_list()
            self.cameraConf.showMaximized()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.mainWidget.videoPlay_Widh = self.mainWidget.videoPlay.size().width()
        self.mainWidget.videoPlay_Height = self.mainWidget.videoPlay.size().height()

    def closeEvent(self, event):
        result = QMessageBox.question(self,
                                      "Confirm Exit...",
                                      "Are you sure you want to exit ?",
                                      QMessageBox.Yes | QtWidgets.QMessageBox.No)
        event.ignore()
        if result == QtWidgets.QMessageBox.Yes:
            currentCamera = self.mainWidget.camList.currentText()
            if currentCamera and currentCamera != "Select Camera":
                try:
                    self.dbMysqlMgr.execute(f"UPDATE camera SET status = 1 WHERE cameName = '{currentCamera}';")
                    print(f"[DB] Saved previously ON camera '{currentCamera}' status = 1 on exit")
                except Exception as e:
                    print(f"[DB Error] saving status on exit: {e}")
            if self.cameraConf is not None:
                self.cameraConf.stopCamera()
            time.sleep(1)
            event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    window = FaceRecogApp()
    sys.exit(app.exec_())

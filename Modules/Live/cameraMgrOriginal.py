from PyQt5.QtCore import QThread
from gui.ConfCamera import *
from PyQt5.QtGui import QImage
import signal
from Modules.Live.displayCameraList import *
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPixmap
from Modules.Live.camera import *
from Modules.Live.CountPopupDetatil import *
from Modules.Live.CRUD_Operation import *
from Modules.Live.DisplayFrameAndObjInfo import *
from datetime import datetime, timedelta


class DrawableLabel(QWidget):
    def __init__(self):
        super(DrawableLabel, self).__init__()
        self.VLayout = QVBoxLayout()
        self.label_image = QLabel("Live Frame Ramesh")
        self.VLayout.addWidget(self.label_image)
        self.setLayout(self.VLayout)


class CameraMgr(QtWidgets.QWidget, Ui_AddCamera):
    def __init__(self, dbMgr, cameraList, cameraSelectionList, configData, parent=None):
        super(CameraMgr, self).__init__(parent)
        self.selected_camera = cameraSelectionList
        self.cameraConf = None
        self.setupUi(self)
        self.setWindowTitle("Camera Details")
        desktop = QApplication.desktop()
        self.desktop_width = desktop.width()
        self.desktop_height = desktop.height()
        self.configData = configData
        self.frameResolution = eval(self.configData.get_frame_resolution())

        self.mainWdgt = parent
        self.dbr = dbMgr
        self.todayCameraCount = dict()
        self.weeklyCameraCount = dict()
        self.monthlyCameraCount = dict()
        self.LastThirtyDaysCameraCount = dict()
        self.bt1.clicked.connect(self.startCamera)
        self.bt_close.clicked.connect(self.closeui)
        self.bt_Add.clicked.connect(self.addCamera)
        self.bt_delete.clicked.connect(self.deleteCamera)
        self.bt_Edit.clicked.connect(self.editCamera)
        # self.cameraLines = dict()
        self.cameraList = cameraList
        self.camerDict = {}
        self.display_cam_list()
        self.inPregress = True
        self.totalTruckExist = 0
        self.dialogPop = None  # Dialog instance
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.set_right_frame()
        self.camera_and_url = dict()
        self.running_camera = dict()
        result = self.dbr.select(f"SELECT cameName,camUrl FROM camera;")
        for cam_url in result:
            self.camera_and_url[cam_url[0]] = cam_url[1]
            self.running_camera[cam_url[0]] = None

            # create CrudOperation instance with self as parent
        self.crud = CrudOperation(self.dbr, parent=self)

        print("CameraMgr constructor is called")

    def getCurrentFrame(self):
        frame = None
        currentCamera = self.mainWdgt.camList.currentText()
        for camname, Cameraobj in self.camerDict.items():
            if camname == currentCamera:
                frame = Cameraobj.orgFrame
                break
        return frame

    def set_right_frame(self):
        DetectFrameRight(self.configData, self.mainWdgt)

    def display_cam_list(self):
        DisplayCameraList(self.cameraList, self.selected_camera, self.list)

    def startCamera(self):

        widget_to_remove = self.mainWdgt.SubLayout.itemAt(0).widget()  # Get the widget at index 0
        self.mainWdgt.SubLayout.removeWidget(widget_to_remove)  # Remove the widget from the layout
        widget_to_remove.deleteLater()
        new_widget = DrawableLabel()
        self.mainWdgt.SubLayout.insertWidget(0, new_widget, 83)  # Insert at index
        try:
            for camname, Cameraobj in self.camerDict.items():
                self.camerDict[camname].progress.disconnect(self.setDisplayFrame)
        except:
            pass

        self.selected_camera.clear()
        if self.mainWdgt.camList.count() > 1:
            first_item = self.mainWdgt.camList.itemText(0)  # Get the text of the first item
            self.mainWdgt.camList.clear()  # Clear all items
            self.mainWdgt.camList.addItem(first_item)

        for row in range(self.list.model().rowCount()):
            index = self.list.model().index(row, 0)  # 0 since QListView is single-column
            widget = self.list.indexWidget(index)
            layout = widget.layout()
            activateCheckbox = layout.itemAt(0).widget()
            if activateCheckbox.isChecked():
                item = self.list.model().itemFromIndex(index)
                if not item.text() in self.selected_camera:
                    self.selected_camera.append(item.text())
                    self.mainWdgt.camList.addItem(item.text())
                else:
                    self.mainWdgt.camList.addItem(item.text())
        self.mainWdgt.camList.setCurrentIndex(1)
        try:
            for camname, Cameraobj in self.camerDict.items():
                if Cameraobj.online:
                    Cameraobj.online = False

            self.camerDict.clear()
            for camdata in self.cameraList:
                if camdata[1] in self.selected_camera:
                    self.camerDict[camdata[1]] = Camera(camdata[0], camdata[1], camdata[2], camdata[3], self.configData,
                                                        self.mainWdgt,
                                                        self.dbr)
            for camname, Cameraobj in self.camerDict.items():
                self.localThread = QThread(parent=self)
                self.camerDict[camname].moveToThread(self.localThread)
                self.localThread.started.connect(self.camerDict[camname].load_network_stream)
                self.camerDict[camname].finished.connect(self.localThread.quit)
                self.camerDict[camname].finished.connect(self.camerDict[camname].deleteLater)
                self.localThread.finished.connect(self.localThread.deleteLater)
                self.camerDict[camname].progress.connect(self.setDisplayFrame)
                self.localThread.start()

                self.close()
            self.closeui()

        except Exception as e:
            print(f"Please select the camera first.{e}")

    def configCamera(self):
        if self.cameraConf is None:
            self.cameraConf = CameraMgr(self.dbr, self.cameraList, self.selected_camera, self.configData, self.mainWdgt)
        else:
            print("camera conf is not none.")
        if len(self.selected_camera) > 0:
            for row in range(self.list.model().rowCount()):
                index = (self.list.model
                         ().index(row, 0))  # 0 since QListView is single-column
                widget = self.list.indexWidget(index)
                layout = widget.layout()
                activateCheckbox = layout.itemAt(0).widget()
                item = self.list.model().itemFromIndex(index)
                if item.text() in self.selected_camera:
                    activateCheckbox.setChecked(True)
        self.cameraConf.showMaximized()

    def config_camera(self):
        self.cameraList.clear()
        data = self.dbr.select("select id, cameName, camUrl, location  from camera where status=1")
        for i, row in enumerate(data):
            self.cameraList.append(row)
        try:
            self.mainWdgt.CameraConf.clicked.disconnect()
        except:
            pass
        self.mainWdgt.CameraConf.clicked.connect(self.configCamera)

        # self.configCamera()
        for camname, Cameraobj in self.camerDict.items():
            self.camerDict[camname].progress.disconnect(self.setDisplayFrame)
        self.closeui()

    def handle_sigint(self, signum, frame):
        self.stopCamera()

    def insertImageIntoDB(self, image, cName, objName):
        im_v = cv2.resize(image, (480, 320), interpolation=cv2.INTER_AREA)
        objimg = cv2.imencode('.jpg', im_v)[1].tobytes()
        today = datetime.today()
        current_date = today.strftime("%d.%m.%Y")
        current_time = today.strftime("%H:%M:%S")
        current_date = str(current_date)
        data_01 = ("Entry", cName, objName, current_date, current_time, objimg)
        sql_insert_blob_query_01 = """INSERT INTO detection(camloc, camera, objectname, date, time, snapshot) 
        VALUES (?, ?, ?, ?, ?, ?)"""
        self.dbr.insert(sql_insert_blob_query_01, data_01)

    def showNewCount(self, totalCount, currentCamera, objectName):
        objectPopupLayout = self.mainWdgt.FrmRecogt.layout().itemAt(0).layout().itemAt(0).layout().itemAt(0).widget()
        objectPopupLayout.info_label.setText(f"{totalCount}")
        if objectName == 'sodium_fire':
            objectIconPath = os.getcwd()
            objectGIFPath = objectIconPath + fr"\popupIcons\fire.gif"
            movie = QMovie(objectGIFPath)
            movie.setScaledSize(QSize(120, 80))
            objectPopupLayout.image_label.setMovie(movie)
            movie.start()
        else:
            objectIconPath = os.getcwd()
            objectGIFPath = objectIconPath + fr"\popupIcons\smoke.gif"
            movie = QMovie(objectGIFPath)
            movie.setScaledSize(QSize(120, 80))
            objectPopupLayout.image_label.setMovie(movie)
            movie.start()
        cameraPoputLayout = self.mainWdgt.FrmRecogt.layout().itemAt(0).layout().itemAt(1).layout().itemAt(0).widget()
        cameraPoputLayout.info_label.setText(f"{currentCamera}")

    def setDisplayFrame(self):
        camCount = self.mainWdgt.camList.count()
        if camCount > 1:
            camname = self.mainWdgt.camList.currentText()
            frame = self.camerDict[camname].get_frame()
            if frame is not None:
                img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
                image = img.scaled(self.frameResolution[0], self.frameResolution[1])
                pix = QPixmap.fromImage(image)
                self.mainWdgt.SubLayout.layout().itemAt(0).setAlignment(Qt.AlignCenter)
                self.mainWdgt.SubLayout.layout().itemAt(0).widget().label_image.setObjectName(f"{camname}")
                self.mainWdgt.SubLayout.layout().itemAt(0).widget().label_image.setPixmap(pix)
            for camname in self.camerDict:
                frame = self.camerDict[camname].get_all_frame_label()
                ob_na = self.camerDict[camname].get_object_name()
                if frame is not None:
                    img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
                    image = img.scaled(220, 200, Qt.KeepAspectRatio)
                    pix = QPixmap.fromImage(image)
                    new_truck = self.camerDict[camname].get_new_truck()
                    if new_truck is not None:
                        self.totalTruckExist += 1
                        self.showNewCount(self.totalTruckExist, camname, ob_na)
                    new_entry_of_material = self.camerDict[camname].get_material_img()

                    # if new_entry_of_material is not None:
                    #     self.insertImageIntoDB(new_entry_of_material, camname, ob_na)
                    DisplayFrame.setImageBottomFrame(self, pix)
                    DisplayFrame.setImageRightFrame(self, pix, camname, ob_na)
        else:
            print("Please select the camera first.")

    def closeui(self):
        self.close()

    def addCamera(self):
        CrudOperation.add_camera(self, self.camera_and_url)

    def deleteCamera(self):
        CrudOperation.delete_camera(self, self.camera_and_url)

    def editCamera(self):
        # CrudOperation.edit_camera(self, self.camera_and_url)
        self.crud.edit_camera(self.camera_and_url)

    def stopCamera(self):
        for camname, Cameraobj in self.camerDict.items():
            if Cameraobj.online:
                Cameraobj.online = False

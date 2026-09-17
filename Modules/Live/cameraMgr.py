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
import cv2
import numpy as np
import io
from PIL import Image

from playsound import playsound
class DrawableLabel(QWidget):
    def __init__(self):
        super(DrawableLabel, self).__init__()
        self.VLayout = QVBoxLayout()
        self.label_image = QLabel("Live Frame Ramesh")
        self.VLayout.addWidget(self.label_image)
        self.setLayout(self.VLayout)


class TelegramSender(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, token, chat_id, photo_path, caption):
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.photo_path = photo_path
        self.caption = caption

    def run(self):
        try:
            url = f'https://api.telegram.org/bot{self.token}/sendPhoto'
            with open(self.photo_path, 'rb') as photo:
                payload = {'chat_id': self.chat_id, 'caption': self.caption}
                files = {'photo': photo}
                requests.post(url, data=payload, files=files, timeout=10)
            self.finished.emit(True)
        except Exception as e:
            print("Telegram send error:", e)
            self.finished.emit(False)

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
        self.camera_with_coordinates = dict()
        self.listOfLinedDrawnCamera = []
        self.frameResolution = eval(self.configData.get_frame_resolution())
        self.telegramTokenId = self.configData.get_telegram_token_id()
        self.telegramChatId = self.configData.get_telegram_chat_id()
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
        self.threadList = []
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
        DisplayCameraList(self.cameraList, self.selected_camera, self.list, dbMgr=self.dbr)

    def startCamera(self):
        if self.mainWdgt.SubLayout.count() > 0:
            item = self.mainWdgt.SubLayout.itemAt(0)
            if item is not None and item.widget() is not None:
                widget_to_remove = item.widget()
                self.mainWdgt.SubLayout.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
        new_widget = DrawableLabel()
        self.mainWdgt.SubLayout.insertWidget(0, new_widget, 83)  # Insert at index
        self.coordinatesOfFrames = self.dbr.select(
            "select id, cameName, xy, x1y1  from camera_frame_coordinates where status=1")
        self.camera_with_coordinates.clear()

        if self.coordinatesOfFrames:
            for data in self.coordinatesOfFrames:
                try:
                    if data[2] and data[3]:
                        self.camera_with_coordinates[data[1]] = [ast.literal_eval(data[2]), ast.literal_eval(data[3])]
                except Exception:
                    pass

        try:
            for camname, Cameraobj in self.camerDict.items():
                self.camerDict[camname].progress.disconnect(self.setDisplayFrame)
        except Exception:
            pass

        for thread in getattr(self, 'threadList', []):
            if thread.isRunning():
                thread.quit()
                thread.wait(300)
        self.threadList.clear()

        self.selected_camera.clear()
        if self.mainWdgt.camList.count() > 1:
            first_item = self.mainWdgt.camList.itemText(0)  # Get the text of the first item
            self.mainWdgt.camList.clear()  # Clear all items
            self.mainWdgt.camList.addItem(first_item)

        if self.list.model():
            for row in range(self.list.model().rowCount()):
                index = self.list.model().index(row, 0)  # 0 since QListView is single-column
                widget = self.list.indexWidget(index)
                if widget:
                    layout = widget.layout()
                    activateCheckbox = layout.itemAt(0).widget()
                    if activateCheckbox.isChecked():
                        item = self.list.model().itemFromIndex(index)
                        if item.text() not in self.selected_camera:
                            self.selected_camera.append(item.text())
                            self.mainWdgt.camList.addItem(item.text())

        if len(self.selected_camera) == 0:
            # Check DB for cameras with status = 1
            active_cams = self.dbr.select("SELECT cameName FROM camera WHERE status = 1;")
            if active_cams:
                for row in active_cams:
                    if row[0] not in self.selected_camera:
                        self.selected_camera.append(row[0])
                        self.mainWdgt.camList.addItem(row[0])

        if len(self.selected_camera) == 0 and len(self.cameraList) > 0:
            first_cam_name = self.cameraList[0][1]
            self.selected_camera.append(first_cam_name)
            self.mainWdgt.camList.addItem(first_cam_name)

        # Update status column in DB: 1 for selected/started, 0 for unselected
        for camdata in self.cameraList:
            cam_name = camdata[1]
            if cam_name in self.selected_camera:
                try:
                    self.dbr.execute(f"UPDATE camera SET status = 1 WHERE cameName = '{cam_name}';")
                    print(f"[DB] Set camera '{cam_name}' status = 1 (started)")
                except Exception as e:
                    print(f"[DB Error] updating status for '{cam_name}': {e}")
            else:
                try:
                    self.dbr.execute(f"UPDATE camera SET status = 0 WHERE cameName = '{cam_name}';")
                    print(f"[DB] Set camera '{cam_name}' status = 0 (unselected)")
                except Exception as e:
                    print(f"[DB Error] updating status for '{cam_name}': {e}")

        idx_to_select = 1
        if len(self.selected_camera) > 0:
            found_idx = self.mainWdgt.camList.findText(self.selected_camera[0])
            if found_idx != -1:
                idx_to_select = found_idx
        if self.mainWdgt.camList.count() > 1:
            self.mainWdgt.camList.setCurrentIndex(idx_to_select)

        try:
            for camname, Cameraobj in self.camerDict.items():
                if Cameraobj.online:
                    Cameraobj.online = False
            self.camerDict.clear()
            for camdata in self.cameraList:
                if camdata[1] in self.selected_camera:
                    try:
                        cameraCoordinate = self.camera_with_coordinates[camdata[1]]
                    except Exception:
                        cameraCoordinate = None
                    self.camerDict[camdata[1]] = Camera(camdata[0], camdata[1], camdata[2], camdata[3], self.configData,
                                                        self.mainWdgt,
                                                        self.dbr, cameraCoordinate)
            for camname, Cameraobj in self.camerDict.items():
                if camname in self.camera_with_coordinates:
                    self.listOfLinedDrawnCamera.append(camname)
                localThread = QThread(parent=self)
                self.camerDict[camname].moveToThread(localThread)
                localThread.started.connect(self.camerDict[camname].load_network_stream)
                self.camerDict[camname].finished.connect(localThread.quit)
                self.camerDict[camname].finished.connect(self.camerDict[camname].deleteLater)
                localThread.finished.connect(localThread.deleteLater)
                self.camerDict[camname].progress.connect(self.setDisplayFrame)
                localThread.start()
                self.threadList.append(localThread)

            self.closeui()

        except Exception as e:
            print(f"Please select the camera first.{e}")

    def configCamera(self):
        self.display_cam_list()
        self.showMaximized()

    def config_camera(self):
        self.cameraList.clear()
        data = self.dbr.select("select id, cameName, camUrl, location, status from camera")
        for i, row in enumerate(data):
            self.cameraList.append(row)
        self.display_cam_list()
        try:
            self.mainWdgt.CameraConf.clicked.disconnect()
        except:
            pass
        self.mainWdgt.CameraConf.clicked.connect(self.configCamera)

        for camname, Cameraobj in self.camerDict.items():
            try:
                self.camerDict[camname].progress.disconnect(self.setDisplayFrame)
            except:
                pass
        self.closeui()

    def handle_sigint(self, signum, frame):
        self.stopCamera()

    # def insertImageIntoDB(self, image, cName, objName):
    #     im_v = cv2.resize(image, (480, 320), interpolation=cv2.INTER_AREA)
    #     objimg = cv2.imencode('.jpg', im_v)[1].tobytes()
    #     today = datetime.today()
    #     current_date = today.strftime("%d.%m.%Y")
    #     current_time = today.strftime("%H:%M:%S")
    #     current_date = str(current_date)
    #     data_01 = ("Entry", cName, objName, current_date, current_time, objimg)
    #     sql_insert_blob_query_01 = """INSERT INTO detection(camloc, camera, objectname, date, time, snapshot)
    #     VALUES (?, ?, ?, ?, ?, ?)"""
    #     self.dbr.insert(sql_insert_blob_query_01, data_01)

    def alert_beep(self, ob_nm):
        if ob_nm == 'no_helmet':
            try:
                playsound('Detection/alerts/helmet.mp3')
            except Exception as e:
                print("Error playing sound:", e)
        if ob_nm == 'no_vest':
            try:
                playsound('Detection/alerts/vest.mp3')
            except Exception as e:
                print("Error playing sound:", e)
        if ob_nm == 'no_safty_shoes':
            try:
                playsound('Detection/alerts/boot.mp3')
            except Exception as e:
                print("Error playing sound:", e)

    # def insertImageIntoDB(self, image, cName, obj_list):
    #     im_v = cv2.resize(image, (480, 320), interpolation=cv2.INTER_AREA)
    #     objimg = cv2.imencode('.jpg', im_v)[1].tobytes()
    #     today = datetime.today()
    #     current_date = today.strftime("%d.%m.%Y")
    #     current_time = today.strftime("%H:%M:%S")
    #     current_date = str(current_date)
    #
    #     data = list()
    #     for missing_ppe in obj_list:
    #         d = ("Entry", cName, None, missing_ppe, current_date, current_time, objimg)
    #         data.append(d)
    #
    #     sql_query = """
    #     INSERT INTO detection (camloc, camera, objectname, missing_ppe, date, time, snapshot)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s)
    #     """
    #
    #     # 👇 call insert_many
    #     self.dbr.insert_many(sql_query, data)
    #     self.alert_beep(obj_list[0])

    def insertImageIntoDB(self, image, cName, obj_list, video_url=None):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(image_rgb)
        max_width = 800
        max_height = 600
        pil_img.thumbnail((max_width, max_height))
        quality = 95
        while True:
            buffer = io.BytesIO()
            pil_img.save(buffer, format="JPEG", quality=quality)
            size_kb = len(buffer.getvalue()) / 1024

            if size_kb <= 120 or quality <= 40:
                break  # stop when under 120 KB or too low quality 
            quality -= 5  # reduce quality gradually
        objimg = buffer.getvalue()
        today = datetime.today()
        current_date = today.strftime("%Y-%m-%d")
        current_time = today.strftime("%H:%M:%S")
        
        # Determine table name based on site_id
        table_name = "detection"
        m_id = None
        s_id = None
        try:
            cam_info = self.dbr.select(f"SELECT machine_id, site_id FROM camera WHERE cameName = '{cName}'")
            if cam_info and len(cam_info) > 0:
                m_id = cam_info[0][0]
                s_id = cam_info[0][1]
                if s_id is not None:
                    # Dynamically generate table name like tbl_detection_1, tbl_detection_2, etc.
                    table_name = f"tbl_detection_{int(s_id)}"
        except Exception as e:
            print("Error checking camera site id:", e)
        
        # Ensure the table exists dynamically before inserting
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            camloc TEXT,
            camera TEXT,
            objectname TEXT,
            missing_ppe TEXT,
            date DATE,
            time TIME,
            snapshot LONGBLOB,
            machine_id INT,
            site_id INT
        )
        """
        try:
            self.dbr.execute(create_table_query)
        except Exception as e:
            print(f"Error checking/creating table {table_name}:", e)

        data = list()
        for missing_ppe in obj_list:
            d = ("Entry", cName, missing_ppe, missing_ppe, current_date, current_time, objimg, m_id, s_id)
            data.append(d)

        sql_query = f"""
        INSERT INTO {table_name} (camloc, camera, objectname, missing_ppe, date, time, snapshot, machine_id, site_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # 👇 call insert_many
        self.dbr.insert_many(sql_query, data)
        self.alert_beep(obj_list[0])


    def showNewCount(self, totalCount, currentCamera, objectName):
        objectPopupLayout = self.mainWdgt.FrmRecogt.layout().itemAt(0).layout().itemAt(0).layout().itemAt(0).widget()
        objectPopupLayout.info_label.setText(f"{totalCount}")
        objectIconPath = os.getcwd()
        # objectGIFPath = objectIconPath + fr"\popupIcons\ppe.png"
        # print('obje name; ', objectGIFPath)
        # print("change ppe")
        # movie = QMovie(objectGIFPath)
        # movie.setScaledSize(QSize(120, 80))
        # objectPopupLayout.image_label.setMovie(movie)
        # if objectName == 'sodium_fire':
        #     objectIconPath = os.getcwd()
        #     objectGIFPath = objectIconPath + fr"\popupIcons\fire.gif"
        #     movie = QMovie(objectGIFPath)
        #     movie.setScaledSize(QSize(120, 80))
        #     objectPopupLayout.image_label.setMovie(movie)
        #     movie.start()
        # else:
        #     objectIconPath = os.getcwd()
        #     objectGIFPath = objectIconPath + fr"\popupIcons\ppe.png"
        #     movie = QMovie(objectGIFPath)
        #     movie.setScaledSize(QSize(120, 80))
        #     objectPopupLayout.image_label.setMovie(movie)
        #     movie.start()
        cameraPoputLayout = self.mainWdgt.FrmRecogt.layout().itemAt(0).layout().itemAt(1).layout().itemAt(0).widget()
        cameraPoputLayout.info_label.setText(f"{currentCamera}")

    def setDisplayFrame(self):
        camCount = self.mainWdgt.camList.count()
        if camCount > 1:
            camname = self.mainWdgt.camList.currentText()
            frame = self.camerDict[camname].get_frame()
            if frame is not None:
                # img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
                # image = img.scaled(self.frameResolution[0], self.frameResolution[1])
                # pix = QPixmap.fromImage(image)
                h, w, ch = frame.shape
                bytes_per_line = frame.strides[0]
                # img = QImage(frame.data, w-200, h-100, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                # pix = QPixmap.fromImage(img)

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
                    # img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
                    # image = img.scaled(220, 200, Qt.KeepAspectRatio)
                    # pix = QPixmap.fromImage(image)
                    h, w, ch = frame.shape
                    bytes_per_line = frame.strides[0]
                    img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                    pix = QPixmap.fromImage(img)
                    # new_truck = self.camerDict[camname].get_new_truck()
                    check_missing_ppe = self.camerDict[camname].get_missing_ppe_list()
                    person_img = self.camerDict[camname].get_material_img()
                    if check_missing_ppe:
                        video_url = self.camerDict[camname].get_record_video_path()
                        self.insertImageIntoDB(person_img, camname, check_missing_ppe, video_url)
                        if len(check_missing_ppe) > 0:
                            self.totalTruckExist += 1
                            self.showNewCount(self.totalTruckExist, camname, ob_na)
                            cwd = os.getcwd()
                            cn = re.sub(r'(?<=[A-Za-z]) (?=\d)|(?<=\d) (?=[A-Za-z])', '_', camname)
                            cn = cn.strip()
                            photo_path = fr"{cwd}\PpeMissingPicture\{cn}\temp_cropped.jpg"

                            # regdt = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            # message = f"Name: {ob_na}\nDate & Time: {regdt}\nLocation: {cn}"
                            #
                            # # Run Telegram sender in background
                            # self.telegram_thread = TelegramSender(self.telegramTokenId, self.telegramChatId, photo_path,
                            #                                       message)
                            # self.telegram_thread.finished.connect(lambda success: print("Telegram sent:", success))
                            # self.telegram_thread.start()

                    # if new_truck is not None:
                    #     self.totalTruckExist += 1
                    #     self.showNewCount(self.totalTruckExist, camname, ob_na)

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
        for thread in getattr(self, 'threadList', []):
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
        self.threadList.clear()

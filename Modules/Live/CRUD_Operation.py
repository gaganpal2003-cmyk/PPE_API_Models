from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLineEdit, QComboBox, \
    QMessageBox


class OperationDialog(QDialog):
    def __init__(self, checkOpe, camera_list):
        super(OperationDialog, self).__init__()

        self.setFixedWidth(550)
        self.check_operation = checkOpe
        self.camAndUrl = camera_list
        self.main_layout = QVBoxLayout()

        self.all_exists_camera = list()
        # self.dbr = Databasemgr()

        if self.check_operation == "add camera":
            self.add_camera()
        elif self.check_operation == "delete camera":
            self.delete_camera()
        elif self.check_operation == "edit camera":
            self.edit_camera()

    def add_camera(self):
        buttonHeight = 30
        buttonWidth = 75
        self.button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet("background-color: green;")
        self.submit_button.setFixedHeight(buttonHeight)
        self.submit_button.setFixedWidth(buttonWidth)
        self.submit_button.clicked.connect(self.submit)
        self.button_layout.addWidget(self.submit_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: red;")
        self.cancel_button.setFixedHeight(buttonHeight)
        self.cancel_button.setFixedWidth(buttonWidth)
        self.cancel_button.clicked.connect(self.cancel)
        self.button_layout.addWidget(self.cancel_button)
        ####
        self.inner_form_layout = QFormLayout()
        self.camera_name_input = QLineEdit()
        self.inner_form_layout.addRow("CAMERA NAME:", self.camera_name_input)
        self.camera_url_input = QLineEdit()
        self.inner_form_layout.addRow("URL:", self.camera_url_input)
        self.main_layout.addLayout(self.inner_form_layout)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def delete_camera(self):
        buttonHeight = 30
        buttonWidth = 75
        self.button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet("background-color: green;")
        self.submit_button.setFixedHeight(buttonHeight)
        self.submit_button.setFixedWidth(buttonWidth)
        self.submit_button.clicked.connect(self.submit)
        self.button_layout.addWidget(self.submit_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: red;")
        self.cancel_button.setFixedHeight(buttonHeight)
        self.cancel_button.setFixedWidth(buttonWidth)
        self.cancel_button.clicked.connect(self.cancel)
        self.button_layout.addWidget(self.cancel_button)
        ####
        self.inner_form_layout = QFormLayout()
        self.camList = QComboBox()
        self.camList.addItem("SELECT CAMERA")
        for cam in list(self.camAndUrl.keys()):
            self.camList.addItem(cam.upper())

        # self.camera_name_input = QLineEdit()
        self.inner_form_layout.addRow("CAMERA NAME:", self.camList)
        self.main_layout.addLayout(self.inner_form_layout)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def updateCameraUrl(self):
        current_item = self.camList.currentText()
        self.current_url.setText(self.camAndUrl[current_item])

    # self.clientListForCrudOpe.currentIndexChanged.connect(self.updateCameraListEdit)

    def edit_camera(self):
        buttonHeight = 30
        buttonWidth = 75
        self.button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet("background-color: green;")
        self.submit_button.setFixedHeight(buttonHeight)
        self.submit_button.setFixedWidth(buttonWidth)
        self.submit_button.clicked.connect(self.submit)
        self.button_layout.addWidget(self.submit_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: red;")
        self.cancel_button.setFixedHeight(buttonHeight)
        self.cancel_button.setFixedWidth(buttonWidth)
        self.cancel_button.clicked.connect(self.cancel)
        self.button_layout.addWidget(self.cancel_button)
        ####
        self.inner_form_layout = QFormLayout()
        self.camList = QComboBox()
        for cam in list(self.camAndUrl.keys()):
            self.camList.addItem(cam)
        print("camAndUrl:- ", self.camAndUrl)
        self.camList.currentIndexChanged.connect(self.updateCameraUrl)
        # self.camera_name_input = QLineEdit()
        self.inner_form_layout.addRow("CURRENT CAMERA:", self.camList)
        self.current_url = QLineEdit(self.camAndUrl[self.camList.currentText()])

        self.inner_form_layout.addRow("CURRENT URL:", self.current_url)

        self.new_camera = QLineEdit()
        self.inner_form_layout.addRow("NEW CAMERA:", self.new_camera)

        self.new_url = QLineEdit()
        self.inner_form_layout.addRow("NEW URL:", self.new_url)

        self.main_layout.addLayout(self.inner_form_layout)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def submit(self):
        self.accept()

    def cancel(self):
        self.reject()

    def getNewCameraUrl(self):
        current_camera = self.camList.currentText()
        current_url = self.current_url.text()
        new_camera = self.new_camera.text()
        new_url = self.new_url.text()
        return current_camera, current_url, new_camera, new_url

    def getCameraAddUrl(self):
        camera_name = self.camera_name_input.text()
        url_name = self.camera_url_input.text()
        return camera_name, url_name

    def getCameraName(self):
        camera_name = self.camList.currentText()
        return camera_name


class CrudOperation(QObject):
    def __init__(self, dbr, parent=None):
        super(CrudOperation, self).__init__(parent)
        self.dbr = dbr
        self.parent_widget = parent  # store parent reference

    def add_camera(self, camera_and_url):
        dialogOperation = OperationDialog("add camera", camera_and_url)
        if dialogOperation.exec_() == QDialog.Accepted:
            camera_name, url_name = dialogOperation.getCameraAddUrl()
            total_camera_list = list(camera_and_url.keys())
            if camera_name in total_camera_list:
                QMessageBox.warning(self, "Input Error", f"{camera_name} already exist.")
            elif len(camera_name) == 0 or len(url_name) == 0:
                QMessageBox.warning(self, "Input Error", "Fill all the field.")
            else:
                cameraDataQuery = f"""INSERT INTO camera(cameName, camUrl) VALUES(?, ?)"""
                self.dbr.insert(cameraDataQuery, (camera_name, url_name,))
                close_dialog = QMessageBox()
                close_dialog.setIcon(QMessageBox.Information)
                close_dialog.setWindowTitle('Closing Window')
                close_dialog.setText(f"Successfully added the camera")
                close_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = close_dialog.exec_()
                self.parent_widget.config_camera()

    def delete_camera(self, camera_and_url):
        dialogOperation = OperationDialog("delete camera", camera_and_url)
        if dialogOperation.exec_() == QDialog.Accepted:
            camera_name = dialogOperation.getCameraName()

            if not camera_name in list(camera_and_url.keys()):
                QMessageBox.warning(self, "Input Error", f"Please select the camera.")
            else:
                close_dialog = QMessageBox()
                close_dialog.setIcon(QMessageBox.Information)
                close_dialog.setWindowTitle('Closing Window')
                close_dialog.setText(f"Do you want to delete camera:- {camera_name}")
                close_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = close_dialog.exec_()

                if result == QMessageBox.Ok:
                    delete_camera_query = f"""DELETE FROM camera WHERE cameName = '{camera_name}';"""
                    self.dbr.exceute(delete_camera_query)
                    close_dialog = QMessageBox()
                    close_dialog.setIcon(QMessageBox.Information)
                    close_dialog.setWindowTitle('Closing Window')
                    close_dialog.setText(f"Successfully deleted the camera: {camera_name}")
                    close_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    result = close_dialog.exec_()
                    self.parent_widget.config_camera()
                elif result == QMessageBox.Cancel:
                    pass

    def edit_camera(self, camera_and_url):
        dialogOperation = OperationDialog("edit camera", camera_and_url)
        if dialogOperation.exec_() == QDialog.Accepted:
            current_camera, current_url, new_camera, new_url = dialogOperation.getNewCameraUrl()
            print('current camera:- ', current_camera)
            print('current url:- ', current_url)
            print('new camera:- ', new_camera)
            print('new url:- ', new_url)
            if len(new_camera) == 0 or len(new_url) == 0:
                QMessageBox.warning(self, "Input Error", "Fill all the field.")
            else:
                close_dialog = QMessageBox()
                close_dialog.setIcon(QMessageBox.Information)
                close_dialog.setWindowTitle('Closing Window')
                close_dialog.setText(
                    f"Do you want edit camera from {current_camera} To {new_camera}")
                close_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                # Capture the button clicked
                result = close_dialog.exec_()

                if result == QMessageBox.Ok:
                    update_camera = f"""UPDATE camera SET cameName = '{new_camera}', camUrl = '{new_url}' WHERE cameName = '{current_camera}';"""
                    self.dbr.exceute(update_camera)

                    close_dialog = QMessageBox()
                    close_dialog.setIcon(QMessageBox.Information)
                    close_dialog.setWindowTitle('Closing Window')
                    close_dialog.setText(
                        f"Successfully edited the camera from {current_camera} To {new_camera}")
                    close_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    result = close_dialog.exec_()
                    self.parent_widget.config_camera()
                elif result == QMessageBox.Cancel:
                    pass
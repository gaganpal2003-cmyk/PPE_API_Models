from PyQt5.QtCore import QObject, QSize, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAbstractItemView, QStyledItemDelegate, QWidget, QCheckBox, QPushButton, QHBoxLayout
import ast

class CustomItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(50, 25)  # Adjust width and height as needed


class CustomWidget(QWidget):
    def __init__(self, checkBoxTrueOrFalse, camName=None, dbMgr=None, parent=None):
        super(CustomWidget, self).__init__(parent)
        self.checkBoxTrueOrFalse = checkBoxTrueOrFalse
        self.camName = camName
        self.dbMgr = dbMgr
        self.cbutton = QCheckBox("Activate")
        if self.checkBoxTrueOrFalse:
            self.cbutton.setChecked(True)
        else:
            self.cbutton.setChecked(False)

        self.cbutton.toggled.connect(self.on_checkbox_toggled)

        self.button = QPushButton("Edit")
        self.button.setEnabled(True)

        self.cbutton.setFixedSize(80, 20)
        self.button.setFixedSize(80, 20)

        lay = QHBoxLayout(self)
        lay.setSpacing(0)
        lay.addWidget(self.cbutton, 30, Qt.AlignCenter)
        lay.setContentsMargins(0, 0, 0, 0)

    def on_checkbox_toggled(self, checked):
        status_val = 1 if checked else 0
        if self.dbMgr and self.camName:
            try:
                self.dbMgr.execute(f"UPDATE camera SET status = {status_val} WHERE cameName = '{self.camName}';")
                print(f"[DB] Updated camera '{self.camName}' status to {status_val}")
            except Exception as e:
                print(f"[DB Error] updating status for '{self.camName}': {e}")


class DisplayCameraList(QObject):
    def __init__(self, cameraList, selected_camera, parent=None, dbMgr=None):
        super(DisplayCameraList, self).__init__(parent)
        self.list = parent
        self.cameraList = cameraList
        self.selected_camera = selected_camera
        self.dbMgr = dbMgr
        self.display_cam_list()

    def display_cam_list(self):
        model = QStandardItemModel()
        self.list.setModel(model)
        delegate = CustomItemDelegate()
        self.list.setItemDelegate(delegate)
        for camdata in self.cameraList:
            item = QStandardItem(camdata[1])
            cam_name = camdata[1]
            cam_status = camdata[4] if len(camdata) > 4 else None
            if cam_status is not None:
                is_active = (cam_status == 1)
            elif self.selected_camera and len(self.selected_camera) > 0:
                is_active = (cam_name in self.selected_camera)
            else:
                is_active = False

            model.appendRow(item)
            self.list.setIndexWidget(item.index(), CustomWidget(is_active, camName=cam_name, dbMgr=self.dbMgr))

        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setSelectionBehavior(QAbstractItemView.SelectRows)
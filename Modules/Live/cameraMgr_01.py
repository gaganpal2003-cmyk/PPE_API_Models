from __future__ import annotations

# -------------------------
# Standard Library Imports
# -------------------------
import os
import sys
from pathlib import Path
from ast import literal_eval
from datetime import datetime, timedelta
from contextlib import suppress

# -------------------------
# Third-Party Imports
# -------------------------
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, Qt, QSize, QObject
from PyQt5.QtGui import QImage, QPixmap, QMovie
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QListView

# -------------------------
# Project Imports
# -------------------------
from gui.ConfCamera import Ui_AddCamera
from Modules.Live.displayCameraList import DisplayCameraList
from Modules.Live.camera import Camera
from Modules.Live.CountPopupDetatil import DetectFrameRight  # (kept import in case it's used elsewhere)
from Modules.Live.CRUD_Operation import CrudOperation
from Modules.Live.DisplayFrameAndObjInfo import DisplayFrame


# -------------------------
# Lightweight helpers / DSA-minded utilities
# -------------------------

def safe_literal_eval_fallback(text: str, default):
    """Safely parse strings like '(1280, 720)' without using eval."""
    try:
        return literal_eval(text)
    except Exception:
        return default


def get_first_checked_items(listview: QListView) -> list[str]:
    """
    Traverse a custom QListView that contains checkboxes in an indexWidget-based layout.
    This performs a single pass O(n) with no extra allocations beyond a list of hits.
    """
    hits = []
    model = listview.model()
    if model is None:
        return hits
    row_count = model.rowCount()
    for row in range(row_count):
        idx = model.index(row, 0)
        widget = listview.indexWidget(idx)
        if not widget:
            continue
        layout = widget.layout()
        if not layout:
            continue
        # 0th item assumed checkbox by original structure
        with suppress(Exception):
            check = layout.itemAt(0).widget()
            if hasattr(check, "isChecked") and check.isChecked():
                item = model.itemFromIndex(idx)
                if item is not None:
                    hits.append(item.text())
    return hits


def get_nested_layout_widget(layout: QtWidgets.QLayout, path: tuple[int, ...]):
    """
    Safely traverse a nested layout by indices (defensive).
    Returns a widget or None.
    """
    current = layout
    for i, index in enumerate(path):
        if not isinstance(current, QtWidgets.QLayout):
            return None
        item = current.itemAt(index)
        if item is None:
            return None
        # If last step, return widget if present, else return layout
        if i == len(path) - 1:
            return item.widget() if item.widget() else item.layout()
        current = item.layout() if item.layout() else item.widget()
    return None


class DrawableLabel(QWidget):
    """Lightweight container for the large live frame preview label."""

    def __init__(self):
        super().__init__()
        self.VLayout = QVBoxLayout(self)
        self.label_image = QLabel("Live Frame Ramesh", self)
        self.label_image.setAlignment(Qt.AlignCenter)
        self.VLayout.addWidget(self.label_image)
        self.setLayout(self.VLayout)


class CameraMgr(QtWidgets.QWidget, Ui_AddCamera):
    """
    Manages camera selection, thread lifecycle, per-camera frames, and UI updates.
    Logic preserved; improved structure, safety, and performance.
    """

    def __init__(self, dbMgr, cameraList, cameraSelectionList, configData, parent=None):
        super().__init__(parent)

        # ---- Core State ----
        self.dbr = dbMgr
        self.cameraList = cameraList  # list of tuples: (id, name, url, location)
        self.selected_camera = set(cameraSelectionList or [])  # use set for O(1) membership
        self.camerDict: dict[str, Camera] = {}  # cam_name -> Camera instance
        self.threadMap: dict[str, QThread] = {}  # cam_name -> QThread
        self.camera_and_url: dict[str, str] = {}  # cam_name -> url
        self.running_camera: dict[str, QThread | None] = {}  # cam_name -> thread or None

        # ---- UI Setup ----
        self.setupUi(self)
        self.setWindowTitle("Camera Details")

        desktop = QApplication.desktop()
        self.desktop_width = desktop.width()
        self.desktop_height = desktop.height()

        self.configData = configData
        # avoid eval; fall back to sensible default
        self.frameResolution = safe_literal_eval_fallback(
            self.configData.get_frame_resolution(), (1280, 720)
        )

        self.mainWdgt = parent

        # Aggregates counters (preserved; dicts kept for O(1) updates/lookups)
        self.todayCameraCount = {}
        self.weeklyCameraCount = {}
        self.monthlyCameraCount = {}
        self.LastThirtyDaysCameraCount = {}

        # UI buttons wiring
        self.bt1.clicked.connect(self.startCamera)
        self.bt_close.clicked.connect(self.closeui)
        self.bt_Add.clicked.connect(self.addCamera)
        self.bt_delete.clicked.connect(self.deleteCamera)
        self.bt_Edit.clicked.connect(self.editCamera)

        # Flags / counters
        self.inPregress = True
        self.totalTruckExist = 0
        self.dialogPop = None

        # Right-side frame init (non-blocking)
        self.set_right_frame()

        # Load camera map from DB
        self._hydrate_camera_url_map()

        # Create CrudOperation instance (reuse same parent window)
        self.crud = CrudOperation(self.dbr, parent=self)

        # Populate the list UI
        self.display_cam_list()

        print("CameraMgr constructor is called")

    # -------------------------
    # DB helpers
    # -------------------------
    def _hydrate_camera_url_map(self) -> None:
        """Read camera name->url from DB safely once and cache."""
        try:
            result = self.dbr.select("SELECT cameName, camUrl FROM camera;")
        except Exception as e:
            print(f"[DB] Failed to load camera urls: {e}")
            result = []

        for cam_name, cam_url in result:
            self.camera_and_url[cam_name] = cam_url
            self.running_camera[cam_name] = None

    # -------------------------
    # UI helpers
    # -------------------------
    def getCurrentFrame(self):
        """Fetch the current frame for the camera selected in mainWdgt.camList."""
        try:
            currentCamera = self.mainWdgt.camList.currentText()
        except Exception:
            return None

        cam_obj = self.camerDict.get(currentCamera)
        return getattr(cam_obj, "orgFrame", None) if cam_obj else None

    def set_right_frame(self):
        """Initialize the right information frame once."""
        try:
            DetectFrameRight(self.configData, self.mainWdgt)
        except Exception as e:
            print(f"[UI] Failed to set right frame: {e}")

    def display_cam_list(self):
        """Fill the left-side camera list with selectable items via project helper."""
        try:
            DisplayCameraList(self.cameraList, list(self.selected_camera), self.list)
        except Exception as e:
            print(f"[UI] Failed to display camera list: {e}")

    # -------------------------
    # Cameras lifecycle
    # -------------------------
    def startCamera(self):
        """
        Start streaming for all selected cameras.
        Preserves logic: replace top widget with DrawableLabel, reconnect signals, spawn threads.
        """
        # Replace the SubLayout's 0th widget with a fresh DrawableLabel (constant-time ops)
        try:
            sublayout = self.mainWdgt.SubLayout
            if sublayout.count() > 0:
                old_widget = sublayout.itemAt(0).widget()
                if old_widget:
                    sublayout.removeWidget(old_widget)
                    old_widget.deleteLater()
            sublayout.insertWidget(0, DrawableLabel(), 83)
        except Exception as e:
            print(f"[UI] Failed to reset live frame area: {e}")

        # Disconnect previous 'progress' signals for safety (constant-time over current dict size)
        with suppress(Exception):
            for cam_obj in self.camerDict.values():
                cam_obj.progress.disconnect(self.setDisplayFrame)

        # Refresh selection from list (O(n) once)
        try:
            self.selected_camera = set(get_first_checked_items(self.list))
        except Exception as e:
            print(f"[UI] Failed to read selected cameras: {e}")
            self.selected_camera = set()

        # Keep first entry in camList; repopulate with selected
        try:
            camListWidget = self.mainWdgt.camList
            first_item_text = camListWidget.itemText(0) if camListWidget.count() > 0 else ""
            camListWidget.clear()
            if first_item_text:
                camListWidget.addItem(first_item_text)
            for name in self.selected_camera:
                camListWidget.addItem(name)
            # Select the first actual camera if present
            if camListWidget.count() > 1:
                camListWidget.setCurrentIndex(1)
        except Exception as e:
            print(f"[UI] Failed to refresh camList widget: {e}")

        # Tear down previous cameras/threads quickly
        try:
            for cam_obj in self.camerDict.values():
                cam_obj.online = False
            self.camerDict.clear()
        except Exception as e:
            print(f"[Lifecycle] Failed to clear previous camera dict: {e}")

        # Build new Camera objects for selected names (single pass through cameraList)
        try:
            selected = self.selected_camera
            # Build a fast lookup by name for cameraList (id, name, url, location)
            name_to_row = {row[1]: row for row in self.cameraList}
            for cam_name in selected:
                row = name_to_row.get(cam_name)
                if not row:
                    continue
                cam_id, name, url, loc = row
                self.camerDict[name] = Camera(cam_id, name, url, loc, self.configData, self.mainWdgt, self.dbr)
        except Exception as e:
            print(f"[Lifecycle] Failed to instantiate cameras: {e}")

        # Spawn a QThread per camera and connect signals
        try:
            # Clean up any existing threads that are not running
            for cname, th in list(self.threadMap.items()):
                if th is None or not th.isRunning():
                    with suppress(Exception):
                        th.quit()
                        th.wait(100)
                    self.threadMap.pop(cname, None)

            # Start threads for current set
            for camname, cam_obj in self.camerDict.items():
                th = QThread(parent=self)
                cam_obj.moveToThread(th)

                # Connect life-cycle signals (unique to avoid duplicates)
                with suppress(Exception):
                    th.started.connect(cam_obj.load_network_stream, type=Qt.UniqueConnection)
                    cam_obj.finished.connect(th.quit, type=Qt.UniqueConnection)
                    cam_obj.finished.connect(cam_obj.deleteLater, type=Qt.UniqueConnection)
                    th.finished.connect(th.deleteLater, type=Qt.UniqueConnection)
                    cam_obj.progress.connect(self.setDisplayFrame, type=Qt.UniqueConnection)

                # Start thread
                th.start()
                self.threadMap[camname] = th
                self.running_camera[camname] = th

            # In original code these two were called after starting threads
            with suppress(Exception):
                self.close()
            self.closeui()

        except Exception as e:
            print(f"[Threads] Error launching camera threads: {e}")

    def configCamera(self):
        """Open configuration dialog for selected cameras; re-check the selected items."""
        try:
            if not hasattr(self, "cameraConf") or self.cameraConf is None:
                self.cameraConf = CameraMgr(self.dbr, self.cameraList, list(self.selected_camera), self.configData,
                                            self.mainWdgt)

            # Sync checked state for selected cameras
            if self.selected_camera:
                model = self.list.model()
                if model:
                    for row in range(model.rowCount()):
                        idx = model.index(row, 0)
                        item = model.itemFromIndex(idx)
                        if item and item.text() in self.selected_camera:
                            widget = self.list.indexWidget(idx)
                            if widget and widget.layout():
                                with suppress(Exception):
                                    check = widget.layout().itemAt(0).widget()
                                    if hasattr(check, "setChecked"):
                                        check.setChecked(True)

            self.cameraConf.showMaximized()
        except Exception as e:
            print(f"[Config] Failed to open camera configuration: {e}")

    def config_camera(self):
        """Refresh camera list from DB, re-hook CameraConf button, and close dialog."""
        try:
            self.cameraList.clear()
            data = self.dbr.select("SELECT id, cameName, camUrl, location FROM camera WHERE status=1")
            for row in data:
                self.cameraList.append(row)
        except Exception as e:
            print(f"[DB] Failed to reload camera config: {e}")

        # Reconnect button
        with suppress(Exception):
            self.mainWdgt.CameraConf.clicked.disconnect()
        with suppress(Exception):
            self.mainWdgt.CameraConf.clicked.connect(self.configCamera)

        # Disconnect live signal to avoid ghost updates
        with suppress(Exception):
            for cam_obj in self.camerDict.values():
                cam_obj.progress.disconnect(self.setDisplayFrame)

        self.closeui()

    # -------------------------
    # System signals / stopping
    # -------------------------
    def handle_sigint(self, signum, frame):
        self.stopCamera()

    def stopCamera(self):
        """Stop all camera threads quickly and safely."""
        # Flip camera.online flags
        for cam_obj in self.camerDict.values():
            with suppress(Exception):
                cam_obj.online = False

        # Stop and clean threads
        for camname, th in list(self.threadMap.items()):
            if th and th.isRunning():
                with suppress(Exception):
                    th.quit()
                    th.wait(200)
            self.threadMap.pop(camname, None)
            self.running_camera[camname] = None

    # -------------------------
    # DB Inserts
    # -------------------------
    def insertImageIntoDB(self, image, cName: str, objName: str):
        """Downscale image and store as BLOB with timestamp."""
        with suppress(Exception):
            import cv2  # keep import local to reduce cold-start overhead when unused

            im_v = cv2.resize(image, (480, 320), interpolation=cv2.INTER_AREA)
            objimg = cv2.imencode('.jpg', im_v)[1].tobytes()

            today = datetime.now()
            current_date = today.strftime("%d.%m.%Y")
            current_time = today.strftime("%H:%M:%S")

            data_01 = ("Entry", cName, objName, current_date, current_time, objimg)
            sql = """INSERT INTO detection(camloc, camera, objectname, date, time, snapshot) 
                     VALUES (?, ?, ?, ?, ?, ?)"""
            try:
                self.dbr.insert(sql, data_01)
            except Exception as e:
                print(f"[DB] insertImageIntoDB failed: {e}")

    # -------------------------
    # UI Popups / counters
    # -------------------------
    def showNewCount(self, totalCount: int, currentCamera: str, objectName: str):
        """
        Update the popup widgets with new counts and show a GIF depending on object type.
        """
        try:
            # object popup: FrmRecogt -> item(0) -> layout -> item(0) -> layout -> item(0) -> widget()
            objectPopupLayout = get_nested_layout_widget(
                self.mainWdgt.FrmRecogt.layout(),
                (0, 0, 0)  # matches original traversal .itemAt(0).layout().itemAt(0).layout().itemAt(0).widget()
            )
            if objectPopupLayout and hasattr(objectPopupLayout, "info_label"):
                objectPopupLayout.info_label.setText(f"{totalCount}")

            # choose gif
            base = Path.cwd() / "popupIcons"
            gif_name = "fire.gif" if objectName == "sodium_fire" else "smoke.gif"
            gif_path = base / gif_name

            if objectPopupLayout and hasattr(objectPopupLayout, "image_label") and gif_path.exists():
                movie = QMovie(str(gif_path))
                movie.setScaledSize(QSize(120, 80))
                objectPopupLayout.image_label.setMovie(movie)
                movie.start()

            # camera popup: FrmRecogt -> item(0) -> layout -> item(1) -> layout -> item(0) -> widget()
            cameraPopupLayout = get_nested_layout_widget(
                self.mainWdgt.FrmRecogt.layout(),
                (0, 1, 0)
            )
            if cameraPopupLayout and hasattr(cameraPopupLayout, "info_label"):
                cameraPopupLayout.info_label.setText(f"{currentCamera}")

        except Exception as e:
            print(f"[UI] showNewCount failed: {e}")

    # -------------------------
    # Frame updates (hot path)
    # -------------------------
    def setDisplayFrame(self):
        """
        Hot path: update the big preview frame for the currently selected camera,
        and update small frames + counters for all cameras.
        Critical path optimized to avoid redundant work.
        """
        try:
            camListWidget = self.mainWdgt.camList
            camCount = camListWidget.count()
        except Exception:
            print("[UI] camList not available.")
            return

        if camCount <= 1:
            print("Please select the camera first.")
            return

        current_camname = camListWidget.currentText()

        # 1) Update main large preview with current camera's latest frame
        cam_obj = self.camerDict.get(current_camname)
        if cam_obj:
            frame = cam_obj.get_frame()
            if frame is not None:
                try:
                    img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
                    image = img.scaled(self.frameResolution[0], self.frameResolution[1], Qt.KeepAspectRatio)
                    pix = QPixmap.fromImage(image)

                    # SubLayout[0] is our DrawableLabel
                    sublayout = self.mainWdgt.SubLayout
                    item0 = sublayout.itemAt(0)
                    if item0 and item0.widget() and hasattr(item0.widget(), "label_image"):
                        item0.setAlignment(Qt.AlignCenter)
                        item0.widget().label_image.setObjectName(f"{current_camname}")
                        item0.widget().label_image.setPixmap(pix)
                except Exception as e:
                    print(f"[UI] Failed to update main preview: {e}")

        # 2) Update bottom/right frames & counters for all cameras (single pass)
        #    Kept the original per-camera logic. Minimal allocations and repeated work avoided.
        for camname, cam_obj in self.camerDict.items():
            try:
                small_frame = cam_obj.get_all_frame_label()
                ob_na = cam_obj.get_object_name()

                if small_frame is not None:
                    img = QImage(small_frame, small_frame.shape[1], small_frame.shape[0],
                                 QImage.Format_RGB888).rgbSwapped()
                    image = img.scaled(220, 200, Qt.KeepAspectRatio)
                    pix = QPixmap.fromImage(image)

                    # Detect "new truck" events
                    new_truck = cam_obj.get_new_truck()
                    if new_truck is not None:
                        self.totalTruckExist += 1
                        self.showNewCount(self.totalTruckExist, camname, ob_na)

                    # material entry image (kept commented as in original)
                    # new_entry_of_material = cam_obj.get_material_img()
                    # if new_entry_of_material is not None:
                    #     self.insertImageIntoDB(new_entry_of_material, camname, ob_na)

                    # Update bottom and right side frames
                    with suppress(Exception):
                        DisplayFrame.setImageBottomFrame(self, pix)
                    with suppress(Exception):
                        DisplayFrame.setImageRightFrame(self, pix, camname, ob_na)
            except Exception as e:
                print(f"[UI] Failed to update side frames for {camname}: {e}")

    # -------------------------
    # Window helpers
    # -------------------------
    def closeui(self):
        with suppress(Exception):
            self.close()

    # -------------------------
    # CRUD operations
    # -------------------------
    def addCamera(self):
        """Open dialog to add a new camera, passing cached name->url map."""
        try:
            CrudOperation.add_camera(self, self.camera_and_url)
        except Exception as e:
            print(f"[CRUD] addCamera failed: {e}")

    def deleteCamera(self):
        """Open dialog to delete a camera."""
        try:
            CrudOperation.delete_camera(self, self.camera_and_url)
        except Exception as e:
            print(f"[CRUD] deleteCamera failed: {e}")

    def editCamera(self):
        """
        Edit a camera using the instance method (preferred) that was already set up with self as parent.
        """
        try:
            self.crud.edit_camera(self.camera_and_url)
        except Exception as e:
            print(f"[CRUD] editCamera failed: {e}")

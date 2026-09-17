from PyQt5.QtChart import QChartView, QBarSet, QBarSeries, QChart, QBarCategoryAxis, QValueAxis, QAbstractBarSeries
from PyQt5.QtCore import QStringListModel, QRect, QTime, QDate, QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QDateEdit, QFormLayout, QGraphicsTextItem, QTimeEdit, QComboBox, QRadioButton, \
    QProgressBar, QLabel, QPushButton, QDialog, QMessageBox
from PyQt5 import QtWidgets
import os
from PyQt5.QtGui import QImage, QPainter, QFont, QFontMetrics, QBrush, QColor
from PyQt5.QtPrintSupport import QPrinter
from gui.ReportTab import *
import io
from PIL import Image
from datetime import datetime, timedelta
from .GraphType import *
from .ReportDownload import *
from .SelectFolder import *


class DownloadPopup(QDialog):
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading Report")
        self.setFixedSize(350, 100)
        self.setStyleSheet("background-color: white;")
        self.result = result
        layout = QVBoxLayout()

        # Title label
        self.label = QLabel("Downloading... 0%")
        self.label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 14px;
            }
        """)
        # self.label.setFont(QFont("Arial", 12, QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #009900;
                border-radius: 8px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #009900;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        # Timer to simulate download progress
        self.progress_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update every 100 ms

    def update_progress(self):
        self.progress_value += int((self.result / 100) * 100)
        # self.progress_value += 2
        self.progress_bar.setValue(self.progress_value)
        self.label.setText(f"Downloading... {self.progress_value}%")

        if self.progress_value >= 100:
            self.progress_bar.setValue(100)
            self.label.setText(f"Downloading... {100}%")

            self.timer.stop()
            self.label.setText("Successfully Downloaded!")
            self.label.setStyleSheet("QLabel { color: black; }")
            QTimer.singleShot(5000, self.accept)


class OperationDialog(QDialog):
    def __init__(self):
        super(OperationDialog, self).__init__()
        self.datetime_edit_from = None
        self.setFixedWidth(250)
        self.setWindowTitle("Please select a date")
        self.main_layout = QVBoxLayout()
        self.add_camera()

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

        self.inner_form_layout = QFormLayout()
        self.datetime_edit_from = QDateEdit(calendarPopup=True)

        self.inner_form_layout.addRow("Select Date:", self.datetime_edit_from)
        # self.inner_form_layout.addRow("","")
        self.main_layout.addLayout(self.inner_form_layout)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)
        ####

    def submit(self):
        self.accept()

    def cancel(self):
        self.reject()

    def getDate(self):
        dateSel = self.datetime_edit_from.currentText()
        return dateSel


class AnalyticData(QObject):
    def __init__(self, dbr, analytics_tab, parent=None):
        super(AnalyticData, self).__init__(parent)

        self.analytics_tab = analytics_tab
        self.dbr = dbr
        self.results = list()

        self.desktop = QApplication.desktop()
        self.table_width = self.desktop.width()
        self.table_height = self.desktop.height()

        self.graph_selection = DisplayGraph(self.dbr, parent=self)
        self.graph_selection.TodayBarChart()

        self.analytics_tab.today.clicked.connect(self.graph_selection.TodayBarChart)
        self.analytics_tab.oneDays.clicked.connect(self.graph_selection.OneDayBarChart)
        self.analytics_tab.sevenDays.clicked.connect(self.graph_selection.SevenDaysBarChart)
        self.analytics_tab.oneMonth.clicked.connect(self.graph_selection.OneMonthBarChart)
        self.dataFilterSection()

        self.report_download_obj = DownloadR(parent=self)

    def download_pdf_excel_layout(self):
        self.bottomFrameData = QVBoxLayout()
        self.bottomFrameData.setAlignment(Qt.AlignTop)
        self.totalSelectedLabel = QLabel("Your total selected data length is:")
        self.totalSelectedLabel.setWordWrap(True)
        self.totalSelectedLabel.setFixedHeight(40)
        self.totalSelectedLabel.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 13px;
                    }
                """)
        self.bottomFrameData.setSpacing(10)
        # self.rptTab.rightLayout.addWidget(self.rptTab.bottomFrame)
        self.bottomFrameData.addWidget(self.totalSelectedLabel)

        self.selectedDataLength = QLabel("0")
        self.selectedDataLength.setAlignment(Qt.AlignCenter)
        # self.selectedDataLength.setWordWrap(True)
        self.selectedDataLength.setFixedHeight(60)
        self.selectedDataLength.setStyleSheet("""
                            QLabel {
                                color: white;
                                font-size: 16px;
                            }
                        """)

        self.bottomFrameData.addWidget(self.selectedDataLength)

        self.reportFormate = QLabel("Please select the report download format:-")
        self.reportFormate.setWordWrap(True)
        self.reportFormate.setFixedHeight(40)
        self.reportFormate.setStyleSheet("""
                            QLabel {
                                color: white;
                                font-size: 13px;
                            }
                        """)
        self.bottomFrameData.addWidget(self.reportFormate)
        self.reportButtons = QHBoxLayout()
        self.excelButton = QRadioButton('Excel')
        self.pdfButton = QRadioButton('PDF')
        self.reportButtons.addWidget(self.excelButton)
        self.reportButtons.addWidget(self.pdfButton)
        self.buttonsContainer = QWidget()
        self.buttonsContainer.setLayout(self.reportButtons)
        self.bottomFrameData.addWidget(self.buttonsContainer, alignment=Qt.AlignCenter)
        self.downloadButton = QPushButton("Download")
        self.downloadButton.clicked.connect(self.generateDocument)
        self.downloadButton.setFixedSize(120, 40)
        self.downloadButton.setStyleSheet("background-color: #008000;")
        self.bottomFrameData.addWidget(self.downloadButton, alignment=Qt.AlignTop | Qt.AlignHCenter)
        self.analytics_tab.bottomFrame.setLayout(self.bottomFrameData)
        # get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
        # print('get wdgt:- ', get_wdgt.text())

    def generateDocument(self):
        if self.pdfButton.isChecked():
            self.pdfButton.setChecked(False)
            self.downloadReport()

    def downloadReportConfirm(self):
        msg_box = QMessageBox()
        msg_box.setStyleSheet(f"""
                                QLabel {{
                                    color: white; /* Sets the text color to red */
                                }}
                                QPushButton {{
                                    color: white; /* Optional: Sets the button text color */
                                }}
                            """)
        msg_box.setWindowTitle("Confirm ?")
        msg_box.setText(f"Are you sure you want to download the report ?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec_()
        if result == QtWidgets.QMessageBox.Yes:
            return 'yes'
        else:
            return 'no'

    def download_pdf_report(self, folder_path, results):
        self.report_download_obj.report_download(folder_path, results)

    def warning_message(self, text):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(f"{text}")
        msgBox.setWindowTitle("Warning ")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.exec()

    def searchResult(self):
        cameraName = self.CameraNameComboBox.currentText()
        objectName = self.ObjectNameComboBox.currentText()

        selectedTimeFrom = self.time_edit_from.time().toString("HH:mm:ss")
        selectedTimeTo = self.time_edit_to.time().toString("HH:mm:ss")
        if selectedTimeFrom == '00:00:00' and selectedTimeTo == '00:00:00':
            selectedTimeTo = '23:59:59'

        selectedDateFrom = self.datetime_edit_from.date().toString("yyyy-MM-dd")
        selectedDateTo = self.datetime_edit_to.date().toString("yyyy-MM-dd")

        if objectName.lower() == 'all' and cameraName.lower() != 'all':
            print(f"object name is all and camera name is {cameraName}")
            self.results = self.dbr.select(
                f"SELECT camera, missing_ppe, date, time, snapshot FROM detection "
                f"WHERE camera = '{cameraName}' "
                f"AND date BETWEEN '{selectedDateFrom}' AND '{selectedDateTo}' "
                f"AND time BETWEEN '{selectedTimeFrom}' AND '{selectedTimeTo}' "
                f"ORDER BY date DESC, time DESC;"
            )
            # self.warning_message("Please select feature name first!")
            print("result:- ", len(self.results))
            get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
            get_wdgt.setText(f"{len(self.results)}")

        if objectName.lower() != 'all' and cameraName.lower() == 'all':
            print(f"object name is {objectName} and camera name is all")
            self.results = self.dbr.select(
                f"SELECT camera, missing_ppe, date, time, snapshot FROM detection "
                f"WHERE missing_ppe = '{objectName}' "
                f"AND date BETWEEN '{selectedDateFrom}' AND '{selectedDateTo}' "
                f"AND time BETWEEN '{selectedTimeFrom}' AND '{selectedTimeTo}' "
                f"ORDER BY date DESC, time DESC;"
            )
            # self.warning_message("Please select feature name first!")
            print("result:- ", len(self.results))
            get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
            get_wdgt.setText(f"{len(self.results)}")

        if objectName.lower() == 'all' and cameraName.lower() == 'all':
            print('object and camera are all')
            self.results = self.dbr.select(
                f"SELECT camera, missing_ppe, date, time, snapshot FROM detection "
                f"WHERE date BETWEEN '{selectedDateFrom}' AND '{selectedDateTo}' "
                f"AND time BETWEEN '{selectedTimeFrom}' AND '{selectedTimeTo}' "
                f"ORDER BY date DESC, time DESC;"
            )
            # self.warning_message("Please select feature name first!")
            print("result:- ", len(self.results))
            get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
            get_wdgt.setText(f"{len(self.results)}")
        if objectName.lower() != 'all' and cameraName.lower() != 'all':
            self.results = self.dbr.select(
                f"SELECT camera, missing_ppe, date, time, snapshot FROM detection "
                f"WHERE camera = '{cameraName}' "
                f"AND missing_ppe = '{objectName}' "
                f"AND date BETWEEN '{selectedDateFrom}' AND '{selectedDateTo}' "
                f"AND time BETWEEN '{selectedTimeFrom}' AND '{selectedTimeTo}' "
                f"ORDER BY date DESC, time DESC;"
            )

            print("result:- ", len(self.results))
            get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
            get_wdgt.setText(f"{len(self.results)}")
        # else:
        #
        #     if objectName.lower() != 'all':
        #         print("ready to select")
        #         # self.results = self.dbr.select(
        #         #     f"SELECT camera, objectname, date, time, snapshot FROM detection WHERE "
        #         #     f"camera = '{cameraName}' AND objectname='{objectName}' AND strftime('%Y-%m-%d', substr("
        #         #     f"date, 7,"
        #         #     f"4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) BETWEEN '"
        #         #     f"{yyyy_from}-{mm_from}-{dd_from}' AND '{yyyy_to}-{mm_to}-{dd_to}' AND time BETWEEN '{selectedTimeFrom}' AND '{selectedTimeTo}' ORDER "
        #         #     f"BY date DESC, time DESC;")
        #         self.results = self.dbr.select(
        #             f"SELECT camera, objectname, date, time, snapshot FROM detection "
        #             f"WHERE camera = '{cameraName}' "
        #             f"AND objectname = '{objectName}' "
        #             f"AND STR_TO_DATE(date, '%d.%m.%Y') BETWEEN '{yyyy_from}-{mm_from}-{dd_from}' AND '{yyyy_to}-{mm_to}-{dd_to}' "
        #             f"AND time BETWEEN '{selectedTimeFrom}' AND '{selectedTimeTo}' "
        #             f"ORDER BY STR_TO_DATE(date, '%d.%m.%Y') DESC, time DESC;"
        #         )
        #
        #
        #         print("result:- ", len(self.results))
        #         get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
        #         get_wdgt.setText(f"{len(self.results)}")

    def downloadReport(self):
        selectedDateFrom = self.datetime_edit_from.text()
        print("result:- ", len(self.results))
        ###
        NewCameraDlg = QtWidgets.QDialog()
        ui = Ui_NewCameraDlg()
        ui.setupUi(NewCameraDlg)

        if NewCameraDlg.exec_() == QtWidgets.QDialog.Accepted:
            # This only runs when "Ok" is clicked
            print('ramesh:- ', ui.getFolderName())
            print("Dialog closed with OK")
            folder_path = ui.getFolderName()
            if len(self.results) > 0:
                reportConfirm = self.downloadReportConfirm()
                if reportConfirm.lower() == 'yes':
                    self.download_popup = DownloadPopup(len(self.results))
                    self.download_popup.show()
                    self.download_pdf_report(folder_path, self.results)
                    self.results.clear()
                else:
                    self.results.clear()
                    pass
            else:
                self.warning_message(f"No data available of date {selectedDateFrom}")
        else:
            print("Dialog canceled")
        ###
        # if len(self.results) > 0:
        #     reportConfirm = self.downloadReportConfirm()
        #     if reportConfirm.lower() == 'yes':
        #         self.download_popup = DownloadPopup(len(self.results))
        #         self.download_popup.show()
        #         self.download_pdf_report(self.results)
        #         self.results.clear()
        #     else:
        #         self.results.clear()
        #         pass
        # else:
        #     self.warning_message(f"No data available of date {selectedDateFrom}")
        # Disconnect the signal before reconnecting it
        # try:
        #     self.downloadButton.clicked.disconnect()
        # except TypeError:
        #     # Signal was not connected before, or already disconnected
        #     pass

    def clearFilter(self):
        default_index = self.ObjectNameComboBox.findText("All")
        if default_index != -1:
            self.ObjectNameComboBox.setCurrentIndex(default_index)

        cam_index = self.CameraNameComboBox.findText("All")
        if cam_index != -1:
            self.CameraNameComboBox.setCurrentIndex(cam_index)

        current_date = QDate.currentDate()
        self.datetime_edit_from.setDate(current_date)
        self.datetime_edit_to.setDate(current_date)

        self.time_edit_from.setTime(QTime(0, 0))
        self.time_edit_to.setTime(QTime(23, 59))
        self.results.clear()
        get_wdgt = self.analytics_tab.bottomFrame.layout().itemAt(1).widget()
        get_wdgt.setText(f"{len(self.results)}")

    def dataFilterSection(self):
        checkTb = self.analytics_tab.layout().itemAt(0).layout().itemAt(0)
        self.report_tab = self.analytics_tab.layout().itemAt(0).layout().itemAt(0).layout()
        #helmet,vest,safety_boot,safety_glasses
        all_object = ["no_helmet", "no_vest", "no_safety_boot"]
        # for i in result_objects:
        #     all_object.append(i[0])

        result_cameras = self.dbr.select("SELECT cameName FROM camera;")
        all_camera = []
        for i in result_cameras:
            all_camera.append(i[0])
        # sorted_cameras = sorted(all_camera, key=lambda x: int(x.split()[1]))
        # data = self.dbr.select("select cameName from camera;")
        # for cam in data:
        #     all_camera.append(cam[0])
        # sorted_cameras = sorted(all_camera, key=lambda x: int(x.split()[1]))
        text_width = 100
        text_height = 40
        label_width = 60
        self.ObjectName = QStringListModel()
        self.ObjectName.setStringList(all_object)

        self.ObjectName.insertRows(0, 1)
        self.ObjectName.setData(self.ObjectName.index(0), "All")

        self.ObjectNameComboBox = QComboBox()
        self.ObjectNameComboBox.setFixedSize(text_width, text_height)
        self.ObjectNameComboBox.setModel(self.ObjectName)
        self.objlable = QLabel('Obj Name')
        self.objlable.setFixedWidth(label_width)

        self.report_tab.addWidget(self.objlable, 1, 0)
        self.report_tab.addWidget(self.ObjectNameComboBox, 1, 1)

        self.CameraName = QStringListModel()
        self.CameraName.setStringList(all_camera)
        self.CameraName.insertRows(0, 1)
        self.CameraName.setData(self.CameraName.index(0), "All")
        self.CameraNameComboBox = QComboBox()
        self.CameraNameComboBox.setModel(self.CameraName)
        self.CameraNameComboBox.setFixedSize(text_width, text_height)
        self.cameralabel = QLabel('Cam Name')
        self.cameralabel.setFixedWidth(label_width)
        self.report_tab.addWidget(self.cameralabel, 2, 0)
        self.report_tab.addWidget(self.CameraNameComboBox, 2, 1)

        self.datetime_edit_from = QDateEdit(calendarPopup=True)
        self.datetime_edit_from.setDisplayFormat("dd-MM-yyyy")
        self.datetime_edit_from.setDate(QDate.currentDate())
        self.datetime_edit_from.setCalendarPopup(True)
        self.datetime_edit_from.setFixedSize(text_width, text_height)
        self.datefromlabel = QLabel('Date:')
        self.datefromlabel.setFixedWidth(label_width)
        self.report_tab.addWidget(self.datefromlabel, 3, 0)
        self.report_tab.addWidget(self.datetime_edit_from, 3, 1)

        self.datetime_edit_to = QDateEdit()
        self.datetime_edit_to.setDisplayFormat("dd-MM-yyyy")
        self.datetime_edit_to.setCalendarPopup(True)
        self.datetime_edit_to.setDate(QDate.currentDate())

        self.datetime_edit_to.setFixedSize(text_width, text_height)
        self.datetolabel = QLabel('To:')
        self.datetolabel.setFixedWidth(label_width)
        self.report_tab.addWidget(self.datetolabel, 4, 0)
        self.report_tab.addWidget(self.datetime_edit_to, 4, 1)

        self.time_edit_from = QTimeEdit()
        self.time_edit_from.setDisplayFormat("HH:mm")
        self.time_edit_from.setMinimumTime(QTime(0, 0))  # Minimum time (00:00)
        self.time_edit_from.setMaximumTime(QTime(23, 59))  # Maximum time (23:59)
        self.time_edit_from.setFixedSize(text_width, text_height)
        self.timefromlabel = QLabel('Time:')
        self.timefromlabel.setFixedWidth(label_width)
        self.report_tab.addWidget(self.timefromlabel, 5, 0)
        self.report_tab.addWidget(self.time_edit_from, 5, 1)

        self.time_edit_to = QTimeEdit()
        self.time_edit_to.setDisplayFormat("HH:mm")
        self.time_edit_to.setMinimumTime(QTime(0, 0))  # Minimum time (00:00)
        self.time_edit_to.setMaximumTime(QTime(23, 59))  # Maximum time (23:59)
        self.time_edit_to.setFixedSize(text_width, text_height)
        self.timetolabel = QLabel('To:')
        self.timetolabel.setFixedWidth(label_width)
        self.report_tab.addWidget(self.timetolabel, 6, 0)
        self.report_tab.addWidget(self.time_edit_to, 6, 1)

        self.clearButton = QPushButton("Clear")
        self.clearButton.clicked.connect(self.clearFilter)
        self.clearButton.setFixedSize(text_width, text_height)
        self.clearButton.setStyleSheet("background-color: #6F8FAF; color: black;")
        self.report_tab.addWidget(self.clearButton, 7, 0)

        self.seeResultButton = QPushButton("Search")
        self.seeResultButton.clicked.connect(self.searchResult)
        self.seeResultButton.setFixedSize(text_width, text_height)
        self.seeResultButton.setStyleSheet("background-color: #20B2AA; color: black;")
        self.report_tab.addWidget(self.seeResultButton, 7, 1)
        self.download_pdf_excel_layout()

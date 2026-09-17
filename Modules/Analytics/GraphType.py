from datetime import datetime, timedelta

from PyQt5.QtChart import QChartView, QChart, QBarSet, QBarSeries, QAbstractBarSeries, QBarCategoryAxis, QValueAxis
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QFont, QColor, QBrush, QPainter
from PyQt5.QtWidgets import QGraphicsTextItem, QApplication, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, \
    QFormLayout, QDateEdit


class DisplayGraph(QObject):
    def __init__(self, dbr, parent=None):
        super(DisplayGraph, self).__init__(parent)
        self.parent_widget = parent
        self.gui_tab = self.parent_widget.analytics_tab
        self.dbr = dbr
        self.lastThirtyDaysNew = dict()
        self.lastSevenDaysNew = dict()
        self.gui_tab.camList.addItem("All")
        cameraQuery = self.dbr.select("SELECT cameName FROM camera ORDER BY id ASC;")
        for cam in cameraQuery:
            self.gui_tab.camList.addItem(cam[0])
        self.gui_tab.camList.currentIndexChanged.connect(self.on_combo_box_click)
        today = datetime.today()
        for i in range(30, 0, -1):
            pastDate = today - timedelta(days=i)
            queryDate = str(pastDate.strftime('%Y-%m-%d'))
            spltDate = queryDate.split('-')
            dDate = f"{spltDate[2]}.{spltDate[1]}.{spltDate[0]}"
            per_camera_data = dict()
            for cam in cameraQuery:
                totalCount = self.dbr.select(
                    f"SELECT count(*) FROM detection WHERE camera='{cam[0]}' AND date='{queryDate}';")
                count_val = totalCount[0][0] if totalCount and len(totalCount) > 0 and len(totalCount[0]) > 0 else 0
                per_camera_data[cam[0]] = count_val
            if i < 8:
                self.lastSevenDaysNew[dDate] = per_camera_data
                self.lastThirtyDaysNew[dDate] = per_camera_data
            else:
                self.lastThirtyDaysNew[dDate] = per_camera_data
        self.desktop = QApplication.desktop()
        self.table_width = self.desktop.width()
        self.table_height = self.desktop.height()

    def on_combo_box_click(self):
        self.changeGraph()

    def changeGraph(self):
        if self.gui_tab.highlighted_button is not None:
            current_camera = self.gui_tab.highlighted_button.text()
            if current_camera == "Today":
                self.TodayBarChart()
            elif current_camera == "1D":
                self.OneDayBarChart()
            elif current_camera == "7D":
                self.SevenDaysBarChart()
            else:
                self.OneMonthBarChart()

    def TodayBarChart(self):
        print("****")
        # self.analytics_tab.layout().itemAt(0).layout().itemAt(0).layout()
        currentGraph = self.gui_tab.layout().itemAt(1).layout().itemAt(1).layout()
        self.clear_layout(currentGraph)
        print("*****")
        tday = datetime.today()
        query_date = str(tday.strftime('%Y-%m-%d'))
        spltDate = query_date.split('-')
        selected_date = f"{spltDate[2]}.{spltDate[1]}.{spltDate[0]}"
        totalBag = self.dbr.select(
            f"SELECT count(*) FROM detection WHERE date='{query_date}';")
        chart_view = QChartView()
        total_count = totalBag[0][0] if totalBag and len(totalBag) > 0 and len(totalBag[0]) > 0 else 0
        if total_count != 0:

            chart = QChart()
            self.timePeriods = ['00-01 AM', '01-02 AM', '02-03 AM', '03-04 AM', '04-05 AM', '05-06 AM', '06-07 AM',
                                '07-08 AM',
                                '08-09 AM', '09-10 AM', '10-11 AM', '11-12 AM', '12-13 PM', '13-14 PM', '14-15 PM',
                                '15-16 PM',
                                '16-17 PM', '17-18 PM', '18-19 PM', '19-20 PM', '20-21 PM', '21-22 PM', '22-23 PM',
                                '23-24 PM']
            lst_of_values = []
            chart.setAnimationOptions(QChart.SeriesAnimations)
            current_camera_name = self.gui_tab.camList.currentText()
            if current_camera_name == 'All':
                for hour in self.timePeriods:
                    time_duration = hour.split()[0].split('-')
                    totalBarPerHour = self.dbr.select(
                        f"SELECT count(*) FROM detection WHERE date='{query_date}' AND time BETWEEN '{time_duration[0]}:00:00' AND '{time_duration[1]}:00:00';")
                    val = totalBarPerHour[0][0] if totalBarPerHour and len(totalBarPerHour) > 0 and len(totalBarPerHour[0]) > 0 else 0
                    lst_of_values.append(val)
            else:
                for hour in self.timePeriods:
                    time_duration = hour.split()[0].split('-')
                    totalBarPerHour = self.dbr.select(
                        f"SELECT count(*) FROM detection WHERE camera='{current_camera_name}' AND date='{query_date}' AND time BETWEEN '{time_duration[0]}:00:00' AND '{time_duration[1]}:00:00';")
                    val = totalBarPerHour[0][0] if totalBarPerHour and len(totalBarPerHour) > 0 and len(totalBarPerHour[0]) > 0 else 0
                    lst_of_values.append(val)
            chart.setTitle(f"PPE Counting Data Analysis - {current_camera_name}")
            chart.setTitleFont(QFont("Arial", 13))
            chart.setTitleBrush(QBrush(QColor("black")))
            chart.setAnimationOptions(QChart.SeriesAnimations)
            set_0 = QBarSet("Hours")
            bar_color = QColor("#016483")
            set_0.setBrush(QBrush(bar_color))
            set_0.setLabelColor(QColor("black"))
            set_0.append(lst_of_values)

            series = QBarSeries()
            # Enable labels on the bars
            series.setLabelsVisible(True)
            series.setLabelsFormat("@value")  # Display the actual value
            series.setLabelsPosition(QAbstractBarSeries.LabelsOutsideEnd)
            series.append(set_0)

            chart.addSeries(series)

            axis_x = QBarCategoryAxis()
            axis_x.append(self.timePeriods)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)

            axis_x.setLabelsAngle(50)
            axis_x.setLabelsFont(QFont("Arial", 8))

            axis_y = QValueAxis()
            axis_y.setTitleText("Total Count")
            axis_y.setLabelsFont(QFont("Arial", 8))
            axis_y.setLabelFormat("%d")
            axis_y.setRange(0, max(lst_of_values) + 50)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)

            # Create a custom title using QGraphicsTextItem
            title_item = QGraphicsTextItem(f"Today's data")
            title_item.setFont(QFont("Arial", 13))
            title_item.setDefaultTextColor(QColor("black"))

            chart_view.setChart(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            desktop = QApplication.desktop()
            width = desktop.width()
            title_item.setPos(width - 180, chart.plotArea().top() - 30)
            chart.scene().addItem(title_item)
            currentGraph.addWidget(chart_view)
        else:
            label = QLabel("Data not available for today!")
            label.setStyleSheet("color: red;")
            label.setAlignment(Qt.AlignHCenter)
            font = QFont()  # Create a QFont object
            font.setPointSize(18)  # Set the font size (e.g., 12 points)
            label.setFont(font)

            currentGraph.addWidget(label)

    def OneDayBarChart(self):

        dialogOperation = QDialog()
        dialogOperation.setWindowTitle("Select Date")
        dialogOperation.setFixedSize(185, 110)
        current_camera_name = self.gui_tab.camList.currentText()

        def submit():
            dialogOperation.accept()

        def cancel():
            dialogOperation.reject()

        main_layout = QVBoxLayout()
        buttonHeight = 30
        buttonWidth = 80
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignBottom)

        submit_button = QPushButton("Submit")
        submit_button.setStyleSheet("background-color: #00A400;")
        submit_button.setFixedHeight(buttonHeight)
        submit_button.setFixedWidth(buttonWidth)
        submit_button.clicked.connect(submit)
        button_layout.addWidget(submit_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("background-color: gray;")
        cancel_button.setFixedHeight(buttonHeight)
        cancel_button.setFixedWidth(buttonWidth)
        cancel_button.clicked.connect(cancel)
        button_layout.addWidget(cancel_button)

        inner_form_layout = QFormLayout()
        datetime_edit_from = QDateEdit(calendarPopup=True)
        datetime_edit_from.setDate(datetime_edit_from.date().currentDate())
        datetime_edit_from.setFixedSize(100, 30)
        datetime_edit_from.setDisplayFormat("dd-MM-yyyy")  # Set display format for date
        inner_form_layout.addRow("Select Date:", datetime_edit_from)

        main_layout.addLayout(inner_form_layout)
        main_layout.addLayout(button_layout)

        dialogOperation.setLayout(main_layout)

        if dialogOperation.exec_() == QDialog.Accepted:
            currentGraph = self.gui_tab.layout().itemAt(1).layout().itemAt(1).layout()
            self.clear_layout(currentGraph)
            selected_date_obj = datetime_edit_from.date()
            query_date = selected_date_obj.toString("yyyy-MM-dd")
            selected_date = selected_date_obj.toString("dd.MM.yyyy")
            totalBag = self.dbr.select(
                f"SELECT count(*) FROM detection WHERE date='{query_date}';")
            total_count = totalBag[0][0] if totalBag and len(totalBag) > 0 and len(totalBag[0]) > 0 else 0
            if total_count != 0:
                chart_view = QChartView()
                chart = QChart()
                self.timePeriods = ['00-01 AM', '01-02 AM', '02-03 AM', '03-04 AM', '04-05 AM', '05-06 AM', '06-07 AM',
                                    '07-08 AM',
                                    '08-09 AM', '09-10 AM', '10-11 AM', '11-12 AM', '12-13 PM', '13-14 PM', '14-15 PM',
                                    '15-16 PM',
                                    '16-17 PM', '17-18 PM', '18-19 PM', '19-20 PM', '20-21 PM', '21-22 PM', '22-23 PM',
                                    '23-24 PM']
                lst_of_values = []
                chart.setAnimationOptions(QChart.SeriesAnimations)
                if current_camera_name == 'All':

                    for hour in self.timePeriods:
                        time_duration = hour.split()[0].split('-')
                        totalBarPerHour = self.dbr.select(
                            f"SELECT count(*) FROM detection WHERE date='{query_date}' AND time BETWEEN '{time_duration[0]}:00:00' AND '{time_duration[1]}:00:00';")
                        val = totalBarPerHour[0][0] if totalBarPerHour and len(totalBarPerHour) > 0 and len(totalBarPerHour[0]) > 0 else 0
                        lst_of_values.append(val)
                else:
                    for hour in self.timePeriods:
                        time_duration = hour.split()[0].split('-')
                        totalBarPerHour = self.dbr.select(
                            f"SELECT count(*) FROM detection WHERE camera='{current_camera_name}' AND date='{query_date}' AND time BETWEEN '{time_duration[0]}:00:00' AND '{time_duration[1]}:00:00';")
                        val = totalBarPerHour[0][0] if totalBarPerHour and len(totalBarPerHour) > 0 and len(totalBarPerHour[0]) > 0 else 0
                        lst_of_values.append(val)
                chart.setTitle(f"PPE Counting Data Analysis - {current_camera_name}")
                chart.setTitleFont(QFont("Arial", 13))
                chart.setTitleBrush(QBrush(QColor("black")))
                chart.setAnimationOptions(QChart.SeriesAnimations)
                set_0 = QBarSet("Hours")
                bar_color = QColor("#016483")
                set_0.setBrush(QBrush(bar_color))
                set_0.setLabelColor(QColor("black"))
                set_0.append(lst_of_values)
                series = QBarSeries()
                series.setLabelsVisible(True)
                series.setLabelsFormat("@value")  # Display the actual value
                series.setLabelsPosition(QAbstractBarSeries.LabelsOutsideEnd)
                series.append(set_0)
                chart.addSeries(series)
                axis_x = QBarCategoryAxis()
                axis_x.append(self.timePeriods)
                chart.addAxis(axis_x, Qt.AlignBottom)
                series.attachAxis(axis_x)

                axis_x.setLabelsAngle(50)
                axis_x.setLabelsFont(QFont("Arial", 8))

                axis_y = QValueAxis()
                axis_y.setTitleText("Total Count")
                axis_y.setLabelsFont(QFont("Arial", 8))
                axis_y.setLabelFormat("%d")
                axis_y.setRange(0, max(lst_of_values) + 50)
                chart.addAxis(axis_y, Qt.AlignLeft)
                series.attachAxis(axis_y)

                chart.legend().setVisible(True)
                chart.legend().setAlignment(Qt.AlignBottom)
                title_item = QGraphicsTextItem(f"Data of {selected_date}")
                title_item.setFont(QFont("Arial", 13))
                title_item.setDefaultTextColor(QColor("black"))

                chart_view.setChart(chart)
                chart_view.setRenderHint(QPainter.Antialiasing)
                desktop = QApplication.desktop()
                width = desktop.width()
                usable_width = (self.table_width * 13) // 100
                title_item.setPos(width - usable_width, chart.plotArea().top() - 30)
                chart.scene().addItem(title_item)
                currentGraph.addWidget(chart_view)
            else:
                label = QLabel(f"Data not available for {selected_date}")
                label.setStyleSheet("color: white;")
                label.setAlignment(Qt.AlignHCenter)
                font = QFont()  # Create a QFont object
                font.setPointSize(18)  # Set the font size (e.g., 12 points)
                label.setFont(font)
                currentGraph.addWidget(label)

    def SevenDaysBarChart(self):
        currentGraph = self.gui_tab.layout().itemAt(1).layout().itemAt(1).layout()
        self.clear_layout(currentGraph)
        current_camera_name = self.gui_tab.camList.currentText()
        lastSevenDays = list(self.lastSevenDaysNew.keys())
        lst_of_values = []
        if current_camera_name == 'All':
            for dt in self.lastSevenDaysNew:
                dt_sum = sum(list(self.lastSevenDaysNew[dt].values()))
                lst_of_values.append(dt_sum)
        else:
            for dt in self.lastSevenDaysNew:
                value = self.lastSevenDaysNew[dt].get(current_camera_name, 0)
                lst_of_values.append(value)

        chart_view = QChartView()
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)

        chart.setTitle(f"PPE Data Analysis - {current_camera_name}")  # Initially set an empty title
        chart.setTitleFont(QFont("Arial", 13))
        chart.setTitleBrush(QBrush(QColor("black")))
        set_0 = QBarSet("Last 7 Days")
        bar_color = QColor("#01BDF8")
        set_0.setBrush(QBrush(bar_color))
        set_0.setLabelColor(QColor("black"))
        set_0.append(lst_of_values)

        series = QBarSeries()
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        series.setLabelsPosition(QAbstractBarSeries.LabelsOutsideEnd)
        series.append(set_0)
        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(lastSevenDays)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_x.setLabelsAngle(50)
        axis_x.setLabelsFont(QFont("Arial", 8))

        axis_y = QValueAxis()
        axis_y.setTitleText("Total Count")
        axis_y.setLabelsFont(QFont("Arial", 8))
        axis_y.setLabelFormat("%d")
        axis_y.setRange(0, max(lst_of_values) + 50)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        title_item = QGraphicsTextItem("Last 7 days data")
        title_item.setFont(QFont("Arial", 13))
        title_item.setDefaultTextColor(QColor("black"))

        chart_view.setChart(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        desktop = QApplication.desktop()
        width = desktop.width()
        usable_width = (self.table_width * 13) // 100
        title_item.setPos(width - usable_width, chart.plotArea().top() - 30)
        chart.scene().addItem(title_item)
        currentGraph.addWidget(chart_view)

    def OneMonthBarChart(self):
        currentGraph = self.gui_tab.layout().itemAt(1).layout().itemAt(1).layout()
        self.clear_layout(currentGraph)
        current_camera_name = self.gui_tab.camList.currentText()
        lastThirtyDays = list(self.lastThirtyDaysNew.keys())
        lst_of_values = []

        if current_camera_name == 'All':
            for dt in self.lastThirtyDaysNew:
                dt_sum = sum(list(self.lastThirtyDaysNew[dt].values()))
                lst_of_values.append(dt_sum)
        else:
            for dt in self.lastThirtyDaysNew:
                value = self.lastThirtyDaysNew[dt].get(current_camera_name, 0)
                lst_of_values.append(value)

        chart_view = QChartView()
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)

        chart.setTitle(f"PPE Counting Data Analysis - {current_camera_name}")  # Initially set an empty title
        chart.setTitleFont(QFont("Arial", 13))
        chart.setTitleBrush(QBrush(QColor("black")))
        set_0 = QBarSet("Last 30 Days")
        bar_color = QColor("#013749")
        set_0.setBrush(QBrush(bar_color))
        set_0.setLabelColor(QColor("black"))
        set_0.append(lst_of_values)

        series = QBarSeries()
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        series.setLabelsPosition(QAbstractBarSeries.LabelsOutsideEnd)
        series.append(set_0)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(lastThirtyDays)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_x.setLabelsAngle(50)
        axis_x.setLabelsFont(QFont("Arial", 8))

        axis_y = QValueAxis()
        axis_y.setTitleText("Total Count")
        axis_y.setLabelsFont(QFont("Arial", 8))
        axis_y.setLabelFormat("%d")
        axis_y.setRange(0, max(lst_of_values) + 50)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        title_item = QGraphicsTextItem("Last 30 days data")
        title_item.setFont(QFont("Arial", 13))
        title_item.setDefaultTextColor(QColor("black"))

        chart_view.setChart(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        desktop = QApplication.desktop()
        width = desktop.width()
        usable_width = (self.table_width * 13) // 100
        title_item.setPos(width - usable_width, chart.plotArea().top() - 30)

        chart.scene().addItem(title_item)
        currentGraph.addWidget(chart_view)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

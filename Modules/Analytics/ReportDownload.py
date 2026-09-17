import io
import os
from datetime import datetime

from PyQt5.QtCore import QObject, QRect, Qt
from PyQt5.QtGui import QImage, QFont, QFontMetrics, QPainter
from PyQt5.QtPrintSupport import QPrinter
from PIL import Image


class DownloadR(QObject):
    def __init__(self, parent=None):
        super(DownloadR, self).__init__(parent)
        self.parent_widget = parent

    def report_download(self, f_n, results):
        printer = QPrinter(QPrinter.HighResolution)
        today = datetime.today()
        tday = today.strftime('%d-%m-%Y')
        ReportFolder = fr"{os.getcwd()}\ReportData\{tday}"
        ttime = today.strftime('%H_%M_%S')
        filename = f"{ttime}.pdf"
        printer.setOutputFileName(fr"{f_n}\{filename}")
        printer.setPaperSize(QPrinter.A4)
        printer.setOutputFormat(QPrinter.PdfFormat)


        if not os.path.exists(ReportFolder):
            os.makedirs(ReportFolder)

        # filename = f"{ttime}.pdf"
        # printer.setOutputFileName(fr"{ReportFolder}\{filename}")

        img = QImage("1.JPG")
        painter = QPainter()
        painter.begin(printer)
        w = printer.pageRect().width() / 2
        h = printer.pageRect().height() / 2
        xscale = printer.pageRect().width() / w
        yscale = printer.pageRect().height() / h

        if xscale < yscale:
            scale = xscale
        else:
            scale = yscale

        painter.scale(scale, scale)

        font = QFont("Times New Roman", 4)
        fm = QFontMetrics(font)

        painter.setFont(font)
        rtTitle = QRect(100, 0, w, 200)
        title = "Client Name"
        frm = datetime.now().strftime("%d/%m/%Y, %H:%M")
        painter.drawText(rtTitle, Qt.AlignLeft | Qt.AlignBottom, f"Download Report Date: {frm}")
        # painter.drawText(rtTitle, Qt.AlignCenter | Qt.AlignBottom, title)
        # rtimg = QRect(1900, 300, 1200, 250)
        # painter.drawImage(rtimg, img)

        logoIconPath = os.getcwd()
        img = QImage(logoIconPath + fr"\icon\adani_logo.png")
        # Resize the image to desired width and height
        resized_img = img.scaled(1000, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # You can change 1000 and 200
        # Define position on the page
        rtimg = QRect(2150, 100, resized_img.width() + 350, resized_img.height() + 200)
        # Draw the resized image
        painter.drawImage(rtimg, resized_img)
        reportType = QRect(100, 0, w, 1000)  # Adjust the position as needed
        painter.drawText(reportType, Qt.AlignCenter, "PPE Violation - Report")

        if self.parent_widget.time_edit_from.text() == '0:00' and self.parent_widget.time_edit_to.text() == '0:00':
            dateFrom = "From: " + self.parent_widget.datetime_edit_from.text() + "," + '0:00'
            dateTo = "To: " + self.parent_widget.datetime_edit_to.text() + "," + '23:59'
        else:
            dateFrom = "From: " + self.parent_widget.datetime_edit_from.text() + "," + self.parent_widget.time_edit_from.text()
            dateTo = "To: " + self.parent_widget.datetime_edit_to.text() + "," + self.parent_widget.time_edit_to.text()
        second_rtTitle = QRect(100, 0, w, 700)  # Adjust the position as needed
        painter.drawText(second_rtTitle, Qt.AlignLeft | Qt.AlignBottom, dateFrom)
        third_rtTitle = QRect(100, 0, w, 800)  # Adjust the position as needed
        painter.drawText(third_rtTitle, Qt.AlignLeft | Qt.AlignBottom, dateTo)

        _margin = 100
        font.setPointSize(4)
        painter.setFont(font)
        _rowheight = 150
        font.setPointSize(5)
        painter.setFont(font)
        rt = QRect(0, 0, w - 2 * _margin, _rowheight)
        nTop = 800
        rt.moveTo(_margin, nTop)
        painter.setPen(Qt.black)
        _x = _margin

        col_count = 6
        _aRatios = [8, 18, 18, 18, 18, 20]
        # self.column_names = ["S.NO.", "Cam_loc", "Obj_name", "Date", "Time", "Snapshot"]
        _aStrings = ["S.NO", "Camera Location", "Missing PPE", "Date", "Time", "Snapshot"]
        font1 = QFont("Times New Roman", 5, QFont.Bold)

        row_count = 0
        max_rows_per_page = 12

        for k in range(col_count):
            tt = QRect(0, 0, rt.width() * _aRatios[k] / 100, rt.height())
            tt.moveTo(_x, nTop)
            painter.drawRect(tt)
            painter.setFont(font1)
            painter.drawText(tt, Qt.AlignCenter | Qt.TextWordWrap, _aStrings[k])
            _x += tt.width()

        font = QFont("Times New Roman", 5)
        font.setPointSize(5)
        painter.setFont(font)
        nTop += rt.height()
        nIndex = 1

        for res in results:
            if nTop == 0:
                nTop = 600
            _nsize = 12
            pixelsHeight = fm.boundingRect(" ").height() * _nsize * 8
            rt = QRect(0, 0, w - 2 * _margin, pixelsHeight)
            rt.moveTo(_margin, nTop)
            painter.setPen(Qt.black)
            painter.drawRect(rt)
            _x = _margin

            tt = QRect(0, 0, rt.width() * _aRatios[0] / 100, rt.height())
            tt.moveTo(_x, nTop)
            painter.drawRect(tt)

            painter.drawText(tt, Qt.AlignCenter | Qt.TextWordWrap, f"{nIndex}")
            _x += tt.width()

            for k in range(1, col_count):
                tt = QRect(0, 0, rt.width() * _aRatios[k] / 100, rt.height())
                tt.moveTo(_x, nTop)
                painter.drawRect(tt)
                field = ""
                if k == 1:
                    field = str(res[0])
                elif k == 2:
                    field = str(res[1])
                elif k == 3:
                    field = str(res[2])
                elif k == 4:
                    field = str(res[3])
                elif k == 5:
                    photo_path = res[4]
                    byte_image = io.BytesIO(photo_path)
                    image = Image.open(byte_image)
                    q_image = QImage(image.tobytes(), image.width, image.height, QImage.Format_RGB888)
                    painter.drawImage(tt, q_image)

                painter.drawText(tt, Qt.AlignCenter | Qt.TextWordWrap, field)
                _x += tt.width()

            nIndex += 1
            nTop += rt.height()
            row_count += 1
            if row_count >= max_rows_per_page:
                printer.newPage()  # Insert a new page
                nTop = 0  # Reset the vertical position for new page
                row_count = 0  # Reset the row count

        painter.end()
        print(fr"PDF saved successfully: {f_n}\{filename}")

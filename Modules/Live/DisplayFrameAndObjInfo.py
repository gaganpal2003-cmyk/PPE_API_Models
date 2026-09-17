from PyQt5.QtCore import QObject, Qt
from datetime import datetime


class DisplayFrame(QObject):
    def __init__(self, parent=None):
        super(DisplayFrame, self).__init__(parent)
        self.mainWdgt = parent

    def setImageBottomFrame(self, pix):
        """
        This method will setPixmap into the empty bottom image frame.
        First It will check either image frame is empty or not if empty then set
        Pixmap.
        If Image frame is not empty then pop left one and insert latest pixmap.
        (Image frame is not empty mean all frames are contains pixmap.)
        """
        width = 117
        height = 105
        layoutBottom = self.mainWdgt.FrmDetect.layout()
        lengthOfLay = layoutBottom.count()
        item = layoutBottom.itemAt(lengthOfLay - 1)
        image_frame = item.widget()

        if image_frame.image_label.pixmap():
            targetFrame = 0
            sourceFrame = 1
            for i in range(lengthOfLay):
                if i == lengthOfLay - 1:
                    item = layoutBottom.itemAt(targetFrame)
                    image_frame = item.widget()
                    image_frame.image_label.clear()

                    target_image_frame = layoutBottom.itemAt(targetFrame).widget()
                    target_image_frame.image_label.setPixmap(pix.scaled(width, height))
                else:
                    source_image_frame = layoutBottom.itemAt(sourceFrame).widget()
                    source_pixmap = source_image_frame.image_label.pixmap()

                    item = layoutBottom.itemAt(targetFrame)
                    image_frame = item.widget()
                    image_frame.image_label.clear()

                    target_image_frame = layoutBottom.itemAt(targetFrame).widget()
                    target_image_frame.image_label.setPixmap(source_pixmap.scaled(width, height))

                    targetFrame += 1
                    sourceFrame += 1

        else:
            for i in range(lengthOfLay):
                item = layoutBottom.itemAt(i)
                image_frame = item.widget()
                if image_frame.image_label.pixmap() is None:
                    image_frame.image_label.setPixmap(pix.scaled(width, height))

                    break

    def setImageRightFrame(self, pix, cam_name, ob_na):
        """
        This method will setPixmap into the empty right image frame as well as
        will setText.
        First It will check either image frame is empty or not if empty then set
        Pixmap and Text. Right Widget will contain Pixmap and left widget will
        contain text.
        (Image frame is not empty mean all frames are contains pixmap.)
        If Image frame is not empty then pop left one and insert latest pixmap and
        text and right and left widget.
        """
        width = 117
        height = 105
        today = datetime.today()
        current_date = today.strftime("%d.%m.%Y")
        current_time = today.strftime("%H:%M:%S")
        date_time_str = f"{cam_name}\n{current_date}\n{current_time}\n{ob_na}"

        layoutRight = self.mainWdgt.FrmRecogt.layout().itemAt(1).layout()
        lengthOfLayRight = layoutRight.count()
        item = layoutRight.itemAt(lengthOfLayRight - 1).layout().itemAt(0)
        image_frame = item.widget()
        if image_frame.image_label.pixmap():
            targetFrame = 0
            sourceFrame = 1
            for i in range(lengthOfLayRight):
                if i == lengthOfLayRight - 1:
                    vertical_layout = layoutRight.itemAt(targetFrame)
                    item_01 = vertical_layout.layout().itemAt(0)
                    item_02 = vertical_layout.layout().itemAt(1)
                    label = item_01.widget()
                    label_02 = item_02.widget()
                    label.image_label.clear()
                    target_image_frame = layoutRight.itemAt(targetFrame).layout().itemAt(0).widget()
                    target_image_frame.image_label.setPixmap(pix.scaled(width, height))

                    label_02.image_label.setText(date_time_str)
                    label_02.setStyleSheet("color: white; background-color: #313131;")
                    label_02.image_label.setAlignment(Qt.AlignCenter)
                else:
                    vertical_layout = layoutRight.itemAt(sourceFrame)
                    source_image_frame = vertical_layout.layout().itemAt(0).widget()
                    source_pixmap = source_image_frame.image_label.pixmap()
                    source_text_frame = vertical_layout.layout().itemAt(1).widget()
                    source_text = source_text_frame.image_label.text()
                    item = layoutRight.itemAt(targetFrame)
                    image_frame = item.layout().itemAt(0).widget()
                    text_frame = item.layout().itemAt(1).widget()
                    image_frame.image_label.clear()
                    text_frame.image_label.clear()
                    t_f = layoutRight.itemAt(targetFrame)
                    target_image_frame = t_f.layout().itemAt(0).widget()
                    target_image_frame.image_label.setPixmap(source_pixmap.scaled(width, height))
                    target_text_frame = t_f.layout().itemAt(1).widget()
                    target_text_frame.image_label.setText(source_text)

                    targetFrame += 1
                    sourceFrame += 1
        else:
            for i in range(lengthOfLayRight):
                vertical_layout = layoutRight.itemAt(i)
                item_01 = vertical_layout.layout().itemAt(0)
                item_02 = vertical_layout.layout().itemAt(1)
                label = item_01.widget()
                label_02 = item_02.widget()

                if label.image_label.pixmap() is None:
                    label.image_label.setPixmap(pix.scaled(width, height))
                    label_02.image_label.setText(date_time_str)
                    label_02.setStyleSheet("color: white; background-color: #313131;")
                    label_02.image_label.setAlignment(Qt.AlignCenter)
                    break

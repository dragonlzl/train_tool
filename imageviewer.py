import sys

import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QPushButton, QVBoxLayout, QWidget, QLabel, \
    QHBoxLayout, QSizePolicy, QDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QImageReader, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QTimer

from get_service_data import download_image, get_service_data

# 重写一个qlabel，用来显示图片和画框
class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 画框用的参数
        self.rects = []

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        red = QColor(255, 0, 0)

        pixmap = self.pixmap()
        if pixmap:
            # 计算图像在 QLabel 内的偏移量
            x_offset = (self.width() - pixmap.width()) / 2
            y_offset = (self.height() - pixmap.height()) / 2

            for index, rect in enumerate(self.rects):
                adjusted_rect = QRect(rect.topLeft() + QPoint(x_offset, y_offset),
                                      rect.size())
                painter.setPen(QPen(red, 2))
                painter.drawRect(adjusted_rect)
        # self.update()

class ImageViewer(QDialog):
    def __init__(self, parent, category):
        super().__init__()

        self.setWindowTitle(f"{parent} {category} 预览")
        # self.setGeometry(300, 300, 800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.server_data = self.server_data()
        self.image_list = self.get_images_by_category(parent, category)[1]
        self.class_id = self.get_images_by_category(parent, category)[0]

        # # 画框用的参数
        # self.rects = []

        self.index = 0
        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()

        self.image_label = ImageLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)

        vbox.addWidget(self.image_label)

        hbox = QHBoxLayout()
        prev_button = QPushButton("上一张", self)
        prev_button.clicked.connect(self.show_previous_image)
        hbox.addWidget(prev_button)

        next_button = QPushButton("下一张", self)
        next_button.clicked.connect(self.show_next_image)
        hbox.addWidget(next_button)

        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.display_image()

    def server_data(self):
        server_data = None
        # 创建一个 QTimer 实例
        self.timer = QTimer()
        self.timer.setSingleShot(True)  # 设置 QTimer 为一次性触发
        self.timer.timeout.connect(self.handle_timeout)  # 超时时调用 handle_timeout 函数
        self.timer.start(5000)  # 设置超时时间为 5 秒
        try:
            # 获取服务器数据
            server_data = get_service_data()
            self.timer.stop()  # 如果请求成功，停止计时器
        except requests.exceptions.Timeout:
            pass
        return server_data

    def handle_timeout(self):
        QMessageBox.warning(self, "警告", f"获取服务端数据超时")

    def get_images_by_category(self, parent, category):
        # 根据类别获取图片路径列表
        # 在这里，需要通过接口获取服务器数据，然后获取对应类别的图片
        # print(parent, category)
        server_data = self.server_data
        server_data = server_data['data']
        for item in range(len(server_data[parent])):
            if server_data[parent][item]["class_name"] == category:
                class_id = server_data[parent][item]["class_id"]
        image_list = [image for image in download_image(class_id) if image.endswith(".png")]

        # print(image_list)
        return class_id, image_list
        # # 例子
        # if category == "1":
        #     return ["/Users/linzhenlong/PycharmProjects/train_tool/imgtest/2023_04_20_14_42_10.png", "/Users/linzhenlong/PycharmProjects/train_tool/imgtest/2023_04_20_10_08_41.png"]
        # elif category == "2":
        #     return ["/Users/linzhenlong/PycharmProjects/train_tool/imgtest/2023_04_20_10_09_18.png", "/Users/linzhenlong/PycharmProjects/train_tool/imgtest/2023_04_20_10_10_07.png"]

    def display_image(self):
        # print("display_image:", self.image_list)
        server_data = self.server_data
        server_data = server_data['data']
        rect_info_list = []
        if self.image_list:
            image_path = self.image_list[self.index]
            image_basename = image_path.split("/")[-1]

            response = requests.get(image_path)
            image_data = response.content

            for item in server_data.keys():
                for i in range(len(server_data[item])):
                    if image_basename in server_data[item][i].keys():
                        rect_info_list = server_data[item][i]['normalized_info'][image_path]

            if rect_info_list:
                for rect_info in rect_info_list:
                    left_top = rect_info['left_top']
                    right_bottom = rect_info['right_bottom']
                    # 因为默认的图就是缩放到了0.25,所以这里要按比例乘以0.25
                    rect = QRect(QPoint(left_top[0] * 0.25, left_top[1] * 0.25),
                                 QPoint(right_bottom[0] * 0.25,
                                        right_bottom[1] * 0.25))
                    # 根据txt初始化rects画图点列表
                    self.image_label.rects.append(rect)

            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            pixmap = pixmap.scaled(pixmap.size() * 0.25, Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)

            label_size = self.image_label.sizeHint()
            self.resize(label_size)

        # pixmap = QPixmap()
        # pixmap.loadFromData(self.image_data)
        # pixmap = pixmap.scaled(pixmap.size() * 0.25, Qt.KeepAspectRatio)
        # self.image_label.setPixmap(pixmap)

    def show_previous_image(self):
        if self.index > 0:
            self.index -= 1
            self.image_label.rects.clear()
            self.display_image()

    def show_next_image(self):
        if self.index < len(self.image_list) - 1:
            self.index += 1
            self.image_label.rects.clear()
            self.display_image()

    # def paintEvent(self, event):
    #     super().paintEvent(event)
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)
    #     red = QColor(255, 0, 0)
    #
    #     for index, rect in enumerate(self.rects):
    #         painter.setPen(QPen(red, 2))
    #         painter.drawRect(rect)
    #     self.update()
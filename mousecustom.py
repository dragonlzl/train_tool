import os

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import QLabel, QMessageBox

# 获取鼠标位置坐标
from dialog2 import CustomDialog
from new_yaml_dialog import NewYamlDialog
from tool import qrects_to_step_num


class MouseCustom(QLabel):
    def __init__(self, mainwindow_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)

        self.mainwindow_instance = mainwindow_instance

        self.x = None
        self.y = None

        # 是否在绘制模式的默认参数
        self.label_mode = False

        # 标记关闭弹窗前是否正常已经点了确定保存当前标记
        self.is_saved = False

        # 绘制相关参数
        self.pixmap = QPixmap()
        self.rects = []
        self.start_point = None
        self.end_point = None
        self.click_counter = 0
        self.reset_history = []
        self.reset_rect_info_history = []
        self.reset_txt_history = []

        self.one_step_or_two = []
        self.one_step_or_two_history = []

    def mouseMoveEvent(self, event):
        self.x = event.x()
        self.y = event.y()
        self.mainwindow_instance.updata_mouse_pos(self.x, self.y)
        if self.label_mode:
            if event.buttons() & Qt.LeftButton and self.start_point is not None:
                self.end_point = event.pos()
                self.update()

    def mousePressEvent(self, event):
        if self.label_mode:
            if event.button() == Qt.LeftButton:
                self.click_counter += 1
                if self.click_counter == 1:
                    self.start_point = event.pos()
                elif self.click_counter == 2:
                    self.end_point = event.pos()
                    rect = QRect(self.start_point, self.end_point)
                    self.rects.append(rect)
                    self.one_step_or_two.append('one_pos')
                    self.mainwindow_instance.step_record_list.append(rect)
                    self.update()
                    self.open_dialog()
                    self.click_counter = 0
                    self.start_point = None
                    self.end_point = None

    def mouseReleaseEvent(self, event):
        # 如果是第二个点，并且点了关闭dialog，则不画框，且不记录
        if not self.is_saved and self.click_counter == 2:
            return
        if self.label_mode:
            if event.button() == Qt.LeftButton and self.start_point is not None:

                self.leave_point = event.pos()
                if self.leave_point != self.start_point:
                    self.end_point = event.pos()
                    rect = QRect(self.start_point, self.end_point)
                    self.rects.append(rect)
                    self.one_step_or_two.append('two_pos')
                    self.mainwindow_instance.step_record_list.append(rect)
                    self.update()
                    self.open_dialog()
                    self.start_point = None
                    self.end_point = None
                    self.click_counter = 0
                else:
                    self.end_point = event.pos()
                    rect = QRect(self.start_point, self.end_point)
                    self.rects.append(rect)
                    self.one_step_or_two.append('one_pos')
                    self.mainwindow_instance.step_record_list.append(rect)
                    self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        red = QColor(255, 0, 0)
        blue = QColor(0, 0, 255)

        for index, rect in enumerate(self.rects):
            painter.setPen(QPen(red, 2))
            painter.drawRect(rect)
            # 如果有选中的步骤，则边框展示为蓝色
            if self.mainwindow_instance.is_selected_step_item:
                rects_step_list = qrects_to_step_num(self.one_step_or_two, self.mainwindow_instance.current_selected_step_items_index)
                # 判断是否和上次选择的步骤一样
                painter.setPen(QPen(blue, 2))
                for step in rects_step_list:
                    painter.drawRect(self.rects[step])

        if self.start_point is not None and self.end_point is not None:
            painter.setPen(QPen(red, 2))
            painter.drawRect(QRect(self.start_point, self.end_point))
        self.update()

    def last_step(self):

        if self.rects:
            # 如果需要点击两下才画出一个框，那么就需要pop两次，代表一次撤销则消除一个框
            if self.one_step_or_two[-1] == 'one_pos':
                self.reset_history.append(self.rects.pop())
                self.reset_history.append(self.rects.pop())
                self.one_step_or_two_history.append(self.one_step_or_two.pop())
                self.one_step_or_two_history.append(self.one_step_or_two.pop())
            else:
                self.reset_history.append(self.rects.pop())
                self.one_step_or_two_history.append(self.one_step_or_two.pop())

            # self.reset_history.append(self.rects.pop())
            self.reset_rect_info_history.append(self.mainwindow_instance.rect_info_list.pop())
            self.reset_txt_history.append(self.mainwindow_instance.txt_list.pop())
            self.mainwindow_instance.ok_count -= 1
            self.mainwindow_instance.get_step_list()

            self.current_selected_step_items_index = None
            self.mainwindow_instance.is_selected_step_item = False

            # 判断是否在旧图下是否撤回或恢复过，点过的话则存在改动
            if self.mainwindow_instance.viewing_saved_image:
                self.mainwindow_instance.is_changed = True
                self.mainwindow_instance.is_image_saved = False

    def next_step(self):

        if self.reset_history:
            # 同样的，如果需要pop2次才消除一个框，那么就需要append2次，代表一次恢复则恢复一个框
            if self.one_step_or_two_history[-1] == 'one_pos':
                self.rects.append(self.reset_history.pop())
                self.rects.append(self.reset_history.pop())
                self.one_step_or_two.append(self.one_step_or_two_history.pop())
                self.one_step_or_two.append(self.one_step_or_two_history.pop())
            else:
                self.rects.append(self.reset_history.pop())
                self.one_step_or_two.append(self.one_step_or_two_history.pop())

            self.mainwindow_instance.rect_info_list.append(self.reset_rect_info_history.pop())
            self.mainwindow_instance.txt_list.append(self.reset_txt_history.pop())
            self.mainwindow_instance.ok_count += 1
            self.mainwindow_instance.get_step_list()

            # 判断是否在旧图下是否撤回或恢复过，点过的话则存在改动
            if self.mainwindow_instance.viewing_saved_image:
                self.mainwindow_instance.is_image_saved = False
                self.mainwindow_instance.is_changed = True

    def is_label_mode(self):
        if self.mainwindow_instance.selected_device is not None:
            if self.label_mode:
                self.label_mode = False
                self.mainwindow_instance.set_label_button_text('绘制')
            else:
                if not self.mainwindow_instance.paused:
                    self.mainwindow_instance.toggle_pause()
                self.label_mode = True
                self.mainwindow_instance.set_label_button_text('绘制中')
                self.mainwindow_instance.paused = True

    def open_dialog(self):

        # 单人模式下才会执行这部分，多人模式下不会执行
        # todo: 区分单人模式和多人模式
        if self.mainwindow_instance.is_single_mode:
            yaml_path = self.mainwindow_instance.yaml_path_input.text()
            if yaml_path == '' or not os.path.exists(yaml_path):
                self.open_new_yaml_dialog()
            else:
                self.dialog = CustomDialog(mousecustom_instance=self)
                self.dialog.exec_()
        else:
            if not self.mainwindow_instance.server_status:
                QMessageBox.warning(self, "警告", f"获取服务端数据时出错，请重新点击'获取服务器状态'按钮确认服务器状态！")
                self.mainwindow_instance.clear_step()
                return
            else:
                self.dialog = CustomDialog(mousecustom_instance=self)
                self.dialog.exec_()

    def open_new_yaml_dialog(self):
        self.new_yaml_dialog = NewYamlDialog(mousecustom_instance=self)
        self.new_yaml_dialog.exec_()
import copy
import sys
import os
import cv2
import datetime
import numpy as np
import io
import subprocess

import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QScrollArea, \
    QHBoxLayout, QFileDialog, QMessageBox, QLineEdit, QSplitter
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QSize, QRect, QPoint
from PyQt5.QtWidgets import QListWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import QFileSystemWatcher

import yaml_manager
from config import timeout
from get_service_data import get_service_data
from mousecustom import MouseCustom
from screen_widget import ScreenWidget
from tool import save_to_txt, read_txt, get_image_size, read_txt_to_str_list


class MainWindow(QMainWindow):
    def __init__(self, window_size=None):
        super().__init__()

        # 服务器状态确认参数
        self.server_status = False

        # 模式选择参数
        self.is_single_mode = False

        # 其他默认参数
        self.error_reported = False
        self.paused = False
        # 记录所有标签标记记录的list，只记录顺利画出框的
        self.rect_info_list = []
        # 记录所有行为的记录，包括每一次单点
        self.step_record_list = []
        self.rect_info_list_copy = []
        self.rect_info_dict = {}
        # 所有归一化后数据转为str，记录到这个list
        self.txt_list = []
        # 原图像size默认值
        self.img_width = 800
        self.img_height = 600

        # 步骤计次
        self.ok_count = 0

        # 步骤字典{0:[],1:[]}
        # 暂时作用不大，就是提示判断用
        self.step_dict = {}

        self.window_size = window_size
        self.setWindowTitle("Phone Screen in PyQt5")

        # Set up the main layout
        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Set up the control panel layout
        control_panel_layout = QVBoxLayout()

        # 操作区上
        control_up_layout = QVBoxLayout()

        # 展示鼠标坐标相关布局处理，同时，这个需要在右侧画面展示区
        # self.image_label = MouseCustom(self.updata_mouse_pos)
        self.image_label = MouseCustom(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.point_x = self.image_label.x
        self.point_y = self.image_label.y

        self.mouse_point_show = QLabel()
        self.mouse_point_show.setText(f"当前图像坐标：X:{self.point_x} , Y:{self.point_y}")
        self.mouse_point_real_show = QLabel()
        self.mouse_point_real_show.setText(f"实际图像坐标：X:{self.point_x} , Y:{self.point_y}")
        control_up_layout.addWidget(self.mouse_point_show)
        control_up_layout.addWidget(self.mouse_point_real_show)

        # 绘制操作区域
        label_image_layout = QVBoxLayout()

        label_button_layout = QHBoxLayout()
        self.label_button = QPushButton("绘制")
        self.label_button.clicked.connect(self.image_label.is_label_mode)
        label_button_layout.addWidget(self.label_button)

        self.quick_screen_button = QPushButton("快截")
        self.quick_screen_button.clicked.connect(self.quick_screen_shot)
        self.quick_screen_button.setEnabled(False)
        label_button_layout.addWidget(self.quick_screen_button)

        self.last_button = QPushButton("撤销")
        self.last_button.clicked.connect(self.image_label.last_step)
        label_button_layout.addWidget(self.last_button)

        self.next_button = QPushButton("恢复")
        self.next_button.clicked.connect(self.image_label.next_step)
        label_button_layout.addWidget(self.next_button)

        label_image_layout.addLayout(label_button_layout)

        # yaml文件选择区
        # 图片路径输入布局
        yaml_path_choice_layout = QHBoxLayout()

        # 路径输入框
        self.yaml_path_input = QLineEdit()
        self.yaml_path_input.setPlaceholderText("服务器状态")
        yaml_path_choice_layout.addWidget(self.yaml_path_input)

        yaml_path_choice_button_layout = QVBoxLayout()

        # 本地路径选择按钮
        self.change_path_button = QPushButton("yaml本地路径")
        self.change_path_button.clicked.connect(self.choose_yaml_file)
        yaml_path_choice_button_layout.addWidget(self.change_path_button)
        # yaml_path_choice_layout.addWidget(self.change_path_button)

        # 服务路径选择按钮
        self.get_path_button = QPushButton("获取服务器状态")
        self.get_path_button.clicked.connect(self.get_yaml_file_from_server)
        # yaml_path_choice_layout.addWidget(self.get_path_button)
        yaml_path_choice_button_layout.addWidget(self.get_path_button)

        yaml_path_choice_layout.addLayout(yaml_path_choice_button_layout)

        label_image_layout.addLayout(yaml_path_choice_layout)

        # 步骤记录参数
        self.is_selected_step_item = False
        self.current_selected_step_items_index = None
        self.last_selected_step_items_index = None

        # 标记旧图是否被改变
        self.is_changed = False

        # Qrect对象列表的对应实际步骤表，把实时转换的顺序关系传入
        # 2代表一个框构成的必要点为2点，因为存在[1,1,2]的情况，两个1才是1个2
        self.step_list = []

        # 绘制标记记录列表区
        self.control_step_list_widget = QListWidget()
        self.control_step_list_widget.clicked.connect(self.selected_step_item)
        self.get_step_list()

        label_image_layout.addWidget(self.control_step_list_widget)

        self.delete_button = QPushButton('删除步骤')
        self.delete_button.clicked.connect(self.delete_selected_item)

        self.clear_step_button = QPushButton('清空步骤')
        self.clear_step_button.clicked.connect(self.clear_step_confirm)

        label_image_layout.addWidget(self.delete_button)
        label_image_layout.addWidget(self.clear_step_button)

        control_up_layout.addLayout(label_image_layout)

        # 是否已经保存过图片
        self.is_image_saved = False

        # 展示按钮布局处理
        button_layout = QHBoxLayout()

        # Set up the pause/play button
        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_button)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_image)
        button_layout.addWidget(self.save_button)

        control_up_layout.addLayout(button_layout)

        # 图片路径输入布局
        image_path_choice_layout = QHBoxLayout()

        # 路径输入框
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("已选图片路径")
        image_path_choice_layout.addWidget(self.save_path_input)

        # 路径选择按钮
        self.change_path_button = QPushButton("图片路径")
        self.change_path_button.clicked.connect(self.select_save_path)
        image_path_choice_layout.addWidget(self.change_path_button)

        control_up_layout.addLayout(image_path_choice_layout)

        # 历史图片路径列表默认参数
        self.recent_saved_images = []
        # 您可以将10更改为您希望保留的最大历史记录数量
        self.max_recent_saved_images = 10
        self.viewing_saved_image = False
        self.last_saved_image = None
        self.current_image_path = None
        self.last_saved_image_path = None

        # 历史路径展示框
        save_path_layput = QVBoxLayout()
        # Add the recent saved images list
        self.img_save_histroy = QLabel()
        self.img_save_histroy.setText("已存图片路径")
        save_path_layput.addWidget(self.img_save_histroy)

        self.recent_saved_images_list = QListWidget(self)
        self.recent_saved_images_list.itemClicked.connect(self.show_saved_image)
        save_path_layput.addWidget(self.recent_saved_images_list)

        control_up_layout.addLayout(save_path_layput)

        # 历史路径按钮事件绑定
        self.directory_watcher = QFileSystemWatcher(self)
        self.directory_watcher.directoryChanged.connect(self.load_saved_images_from_directory)

        # 操作区下
        control_down_layout = QVBoxLayout()

        # 比例操作按钮
        zoom_button_layout = QHBoxLayout()

        # Add the zoom in button
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        zoom_button_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        zoom_button_layout.addWidget(self.zoom_out_button)

        control_down_layout.addLayout(zoom_button_layout)

        # 缩放默认参数
        self.last_scale_factor = 0.25
        self.scale_factor = 0.25
        self.max_scale_factor = 1.0
        self.min_scale_factor = 0.25
        self.scale_step = 0.05
        self.current_image = None

        # 缩放比例展示
        self.zoom_label = QLabel()
        self.zoom_label.setText(f"缩放比例: {self.scale_factor:.2f}")
        control_down_layout.addWidget(self.zoom_label)

        # 设备连接相关默认参数
        self.device_id = None
        self.selected_device = None
        self.device_list = None
        self.device_connected = False

        # 添加设备列表部件
        self.device_list_widget = QListWidget()
        self.device_list_widget.itemClicked.connect(self.select_device)

        # 刷新设备按钮和设备列表文本布局
        devices_button_layout = QHBoxLayout()

        # 创建刷新设备列表按钮
        self.refresh_devices_button = QPushButton("刷新设备")
        self.refresh_devices_button.clicked.connect(self.refresh_device_list)

        # 在 control_panel_layout 中添加设备列表和刷新设备列表按钮
        devices_button_layout.addWidget(QLabel("设备列表:"))
        devices_button_layout.addWidget(self.refresh_devices_button)
        control_down_layout.addLayout(devices_button_layout)
        control_down_layout.addWidget(self.device_list_widget)

        # 在这里添加一个 QLabel 控件以显示设备 ID
        self.device_id_label = QLabel("当前连接设备 ID: 未连接")
        self.device_id_label.setAlignment(Qt.AlignCenter)
        self.device_id_label.setMinimumHeight(25)

        # 将 device_id_label 添加到 control_layout
        control_down_layout.addWidget(self.device_id_label)

        # 拖动功能实现
        # 操作区上下拖动功能
        splitter_v = QSplitter(Qt.Vertical)

        control_up = self.layout_to_widget(control_up_layout)
        splitter_v.addWidget(control_up)
        control_down = self.layout_to_widget(control_down_layout)
        splitter_v.addWidget(control_down)
        splitter_v.setStretchFactor(0, 1)

        # 把拖动加进操作区布局
        control_panel_layout.addWidget(splitter_v)

        # 画面展示区
        right_image_layout = QHBoxLayout()
        # right_image_layout.addWidget(self.image_label)

        # 可滚动区域，把self.image_label直接放进去
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        right_image_layout.addWidget(self.scroll_area)

        # 实现左右拖动
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.layout_to_widget(control_panel_layout))
        splitter.addWidget(self.layout_to_widget(right_image_layout))
        splitter.setStretchFactor(0, 1)

        # 主布局加入左右拖动控件
        main_layout.addWidget(splitter)

        # 刷新界面的timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000)  # 更新频率，单位：毫秒

        # Set the initial window size
        if self.window_size is not None:
            self.resize(self.window_size)

        # Set the initial splitter sizes
        # Show the window before setting splitter
        self.show()
        splitter.setSizes([self.width() * 1 / 5, self.width() * 4 / 5])
        splitter_v.setSizes([self.height() * 2 / 3, self.height() * 1 / 3])

    # 快速定义widget
    def layout_to_widget(self, layout):
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def quick_screen_shot(self):
        self.qs = ScreenWidget(self)
        self.qs.save_signal_data.connect(self.quick_screen_shot_save)

    def quick_screen_shot_save(self):
        print("save")

    # 初始化各种list
    # def init_list(self):
    #     # 初始化，不然切图会出现重复的框
    #     self.image_label.one_step_or_two.clear()
    #     self.image_label.rects.clear()
    #     self.rect_info_list.clear()
    #
    #     self.image_label.one_step_or_two_history.clear()
    #     self.image_label.reset_history.clear()
    #     self.image_label.reset_rect_info_history.clear()
    #     self.image_label.reset_txt_history.clear()

    def clear_step(self):
        # 清除步骤列表选择
        self.is_selected_step_item = False
        # 清空全部
        self.image_label.one_step_or_two.clear()
        self.image_label.rects.clear()
        self.rect_info_list.clear()
        self.txt_list.clear()

        self.image_label.one_step_or_two_history.clear()
        self.image_label.reset_history.clear()
        self.image_label.reset_rect_info_history.clear()
        self.image_label.reset_txt_history.clear()

        self.get_step_list()

    def clear_step_confirm(self):
        reply = QMessageBox.question(self, "清空步骤", "是否清空步骤？清空不触发自动保存，清空前建议先自行保存", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_step()
        else:
            pass

    def selected_step_item(self):
        self.is_selected_step_item = True
        self.current_selected_step_items_index = self.control_step_list_widget.currentRow()

    def delete_selected_item(self):
        if self.image_label.rects and self.is_selected_step_item:
            # 如果需要点击两下才画出一个框，那么就需要pop两次，代表一次撤销则消除一个框
            if self.image_label.one_step_or_two[-1] == 'one_pos':
                self.image_label.reset_history.append(self.image_label.rects.pop(self.current_selected_step_items_index))
                self.image_label.reset_history.append(self.image_label.rects.pop(self.current_selected_step_items_index))
                self.image_label.one_step_or_two_history.append(self.image_label.one_step_or_two.pop(self.current_selected_step_items_index))
                self.image_label.one_step_or_two_history.append(self.image_label.one_step_or_two.pop(self.current_selected_step_items_index))
            else:
                self.image_label.reset_history.append(self.image_label.rects.pop(self.current_selected_step_items_index))
                self.image_label.one_step_or_two_history.append(self.image_label.one_step_or_two.pop(self.current_selected_step_items_index))

            # self.reset_history.append(self.rects.pop())
            self.image_label.reset_rect_info_history.append(self.rect_info_list.pop(self.current_selected_step_items_index))
            self.image_label.reset_txt_history.append(self.txt_list.pop(self.current_selected_step_items_index))
            self.ok_count -= 1

            self.current_selected_step_items_index = None
            self.is_selected_step_item = False

            # 判断是否在旧图下是否撤回或恢复过，点过的话则存在改动
            if self.viewing_saved_image:
                self.is_changed = True
                self.is_image_saved = False
            self.get_step_list()

    # 展示步骤列表的步骤
    def get_step_list(self):
        items = []
        self.control_step_list_widget.clear()
        # if image_path is not None:
        #     rect_info_list = self.rect_info_dict[image_path]
        # else:
        rect_info_list = self.rect_info_list
        for rect_info in rect_info_list:
            items.append(f"{rect_info['class_id']}, {rect_info['center_point']}, {rect_info['width']}, {rect_info['length']}")
        self.control_step_list_widget.addItems(items)

    def load_classes(self, yaml_path):
        try:
            self.class_data = yaml_manager.yaml_read(yaml_path)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"读取YAML文件时出错: {e}")
            # print(f"读取YAML文件时出错: {e}")

    def choose_yaml_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*);;文本文件 (*.txt)", options=options)

        if file:
            self.yaml_path_input.setText(file)
            self.load_classes(file)

    def get_yaml_file_from_server(self):

        self.timer = QTimer()
        self.timer.setSingleShot(True)  # 设置 QTimer 为一次性触发
        self.timer.timeout.connect(self.handle_timeout)  # 超时时调用 handle_timeout 函数
        self.timer.start(timeout * 1000)  # 设置超时时间为 5 秒

        try:
            get_service_data()
            self.timer.stop()  # 如果请求成功，停止计时器
            self.server_status = True
            self.yaml_path_input.setText("服务端状态：已连接")
        except requests.exceptions.Timeout:
            pass
            # print(f"获取服务端数据时出错: {e}")

    def handle_timeout(self):
        QMessageBox.warning(self, "警告", f"获取服务端数据超时")
        self.server_status = False
        self.yaml_path_input.setText("服务端状态：未连接")



    def set_label_button_text(self, new_text):
        self.label_button.setText(new_text)

    def updata_mouse_pos(self, x=None, y=None):
        self.point_x = x
        self.point_y = y
        if self.point_x and self.point_y:
            self.mouse_point_show.setText(f"当前图像坐标：X:{self.point_x} , Y:{self.point_y}")
            self.mouse_point_real_show.setText(f"实际图像坐标：X:{int(self.point_x/self.scale_factor)} , Y:{int(self.point_y/self.scale_factor)}")

    def check_device_connected(self):
        adb_devices_command = "adb devices"
        result = subprocess.check_output(adb_devices_command, shell=True, text=True)
        devices = result.strip().split('\n')[1:]
        connected_device_ids = [device.split('\t')[0] for device in devices if device.endswith('device')]

        if connected_device_ids:
            return True
        return False

    def refresh_device_list(self):
        # 使用 ADB 获取设备列表
        self.device_list = self.get_device_list()

        # 清空当前设备列表
        self.device_list_widget.clear()

        # 添加设备到设备列表
        for device in self.device_list:
            self.device_list_widget.addItem(device)
        if self.device_list == []:
            self.selected_device = None
            self.device_id_label.setText("当前连接设备 ID: 未连接")
        elif self.selected_device not in self.device_list:
            self.selected_device = None
            self.device_id_label.setText("当前连接设备 ID: 未连接")

    @staticmethod
    def get_device_list():
        adb_command = "adb devices"
        output = subprocess.check_output(adb_command, shell=True).decode()
        lines = output.strip().split('\n')
        devices = [line.split('\t')[0] for line in lines[1:] if line.endswith('\tdevice')]
        return devices

    def select_device(self, item):
        self.selected_device = item.text()
        self.device_id_label.setText(f"设备ID: {self.selected_device}")

    def get_connected_device_id(self):
        # 使用 adb devices 命令获取连接的设备
        adb_command = "adb devices"
        devices_output = subprocess.check_output(adb_command.split()).decode("utf-8").strip().split("\n")[1:]

        # 如果有连接的设备，返回设备 ID
        if devices_output and "device" in devices_output[0]:
            return devices_output[0].split()[0]

        return None

    def select_save_path(self):
        if self.directory_watcher.directories():
            self.directory_watcher.removePaths(self.directory_watcher.directories())
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        save_directory = QFileDialog.getExistingDirectory(self, "选择保存路径", "", options=options)

        if save_directory:
            self.save_path_input.setText(save_directory)
            self.directory_watcher.addPath(save_directory)
            self.load_saved_images_from_directory(save_directory)

    def toggle_pause(self):
        self.refresh_device_list()
        if self.device_list == []:
            self.selected_device = None
            self.device_id_label.setText("当前连接设备 ID: 未连接")
        elif self.selected_device not in self.device_list:
            self.selected_device = None
            self.device_id_label.setText("当前连接设备 ID: 未连接")

        self.devcies_connect_state = self.check_device_connected()

        if not self.devcies_connect_state:
            QMessageBox.warning(self, '提示', '请先连接设备！')
            return
        if self.selected_device is not None:
            self.device_connected = True
            if self.paused:
                if self.rect_info_list:
                    # 如果当前不为查看已保存的图片，则弹窗提示是否保存当前标注
                    if not self.viewing_saved_image:
                        # 如果没有保存过，则弹窗提示是否保存
                        if not self.is_image_saved:
                            save_confirm_dialog = self.confirm_dialog('提示', '是否保存当前标注？不保存将会丢失当前标注！不可恢复')
                            if save_confirm_dialog:
                                # 判断路径是否存在
                                if os.path.exists(self.save_path_input.text()):
                                    self.save_image()
                                    # self.image_label.is_label_mode()
                                else:
                                    QMessageBox.warning(self, '提示', '保存路径不存在，请重新选择保存路径')
                                    return
                            else:
                                self.clear_step()
                            self.image_label.is_label_mode()
                    else:
                        if self.is_changed:
                            if not self.is_image_saved:
                                saved_image_confirm_dialog = self.confirm_dialog('提示',
                                                                                 '是否保存当前标注？不保存将会丢失当前标注！')
                                if saved_image_confirm_dialog:
                                    # 判断路径是否存在
                                    if os.path.exists(self.save_path_input.text()):
                                        self.save_image()
                                        self.current_image_path = None
                                    else:
                                        QMessageBox.warning(self, '提示', '保存路径不存在，请重新选择保存路径')
                                        return
                                else:
                                    self.is_changed = False
                                    # self.clear_step()

                        # 判断是否为绘制状态，如果是则不允许暂停
                        if self.image_label.label_mode:
                            pause_confirm_dialog = self.confirm_dialog('提示', '是否要退出绘制中模式？')
                            # 确认退出的话，就退出绘制中模式，且恢复为继续状态
                            if pause_confirm_dialog:
                                self.image_label.is_label_mode()
                                # 只有修改旧图后点击继续才并且确定退出绘制中才会清空
                                self.clear_step()
                            else:
                                return
                else:
                    # 判断是否为绘制状态，如果是则不允许暂停
                    if self.image_label.label_mode:
                        pause_confirm_dialog = self.confirm_dialog('提示', '是否要退出绘制中模式？')
                        # 确认退出的话，就退出绘制中模式，且恢复为继续状态
                        if pause_confirm_dialog:
                            self.image_label.is_label_mode()
                        else:
                            return

                # # 上面的return都没有触发的话，就是可以暂停的情况
                # self.image_label.rects.clear()
                # # 清空标注步骤信息
                # self.rect_info_list.clear()
                self.clear_step()
                # # 展示步骤信息，当前为空
                # self.get_step_list()
                self.paused = False
                self.pause_button.setText('暂停')
                self.is_image_saved = False
            else:
                self.paused = True
                self.pause_button.setText('继续')
        else:
            self.device_connected = False
            QMessageBox.warning(self, '提示', '请先连接设备！')
            return

    # 二次确认弹窗，确认则返回True，否则返回False
    def confirm_dialog(self, title, text):
        reply = QMessageBox.question(self, title, text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def save_image(self):
        if not self.txt_list and not self.rect_info_list:
            QMessageBox.warning(self, "警告", "需要进行标注才能保存")
            self.is_changed = False
            return

        if not self.paused:
            QMessageBox.warning(self, "警告", "需要先暂停界面")
            return

        save_path = self.save_path_input.text()
        if save_path:
            dir_path = os.path.dirname(save_path)
            if not os.path.exists(dir_path):
                QMessageBox.critical(self, "失败", "指定的目录不存在，请检查保存路径")
                return

            if not save_path.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                # 默认添加以当前时间戳命名的 .png 文件
                save_path += f'/{timestamp}.png'

            # 如果当前不是展示历史图片，则保存时要保存当前图片，否则不保存且读取txt名字，再覆盖该txt
            if not self.viewing_saved_image:
                success = cv2.imwrite(save_path, self.current_image)
            else:
                if self.current_image_path != self.last_saved_image_path:
                    save_path = self.last_saved_image_path
                else:
                    # 根据当前选择历史图片路径，重写对应的txt
                    save_path = self.current_image_path
                success = True

            try:
                if not save_to_txt(self.txt_list, save_path):
                    QMessageBox.warning(self, "警告", f"写入txt文件失败")

                # 保存后要清掉红框和各个缓存
                # self.image_label.rects = []
                # self.txt_list = []
                # self.ok_count = 0
                # self.rect_info_list = []

            except Exception as e:
                QMessageBox.warning(self, "警告", f"写入文件txt出错: {e}")

            if success:
                self.is_changed = False
                self.is_image_saved = True
                QMessageBox.information(self, "成功", "成功保存")
            else:
                QMessageBox.critical(self, "失败", "保存失败，请检查路径和图像格式")
        else:
            QMessageBox.warning(self, "警告", "请指定保存路径")

    def change_save_path(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "更改保存路径", "", "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*)")
        if save_path:
            self.save_path_input.setText(save_path)

    def update_frame(self):
        if self.paused:
            return
        image = self.get_image_from_phone()
        if image is not None:
            if image is not None:
                self.error_reported = False
                self.current_image = image.copy()
                self.device_connected = True

                height, width, channel = image.shape
                self.current_height = height
                self.current_width = width
                bytes_per_line = 3 * width
                qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage.rgbSwapped())

                self.img_width = pixmap.width()
                self.img_height = pixmap.height()

                pixmap = pixmap.scaled(pixmap.width() * self.scale_factor, pixmap.height() * self.scale_factor,
                                       Qt.KeepAspectRatio)

                self.image_label.setPixmap(pixmap)
                self.image_label.adjustSize()

                if self.window_size is None:
                    self.scroll_area.setWidgetResizable(True)
                self.viewing_saved_image = False
            else:
                self.device_connected = False
                if not self.error_reported:
                    self.check_device_connected()
                    self.error_reported = True
        else:
            self.device_connected = False
            if not self.error_reported:
                QMessageBox.warning(self, "警告", "请先连接设备")
                self.toggle_pause()
                self.error_reported = True

    def get_image_from_phone(self):
        if not self.selected_device:
            # 如果没有选中的设备，返回 None
            return None
        device_id = self.selected_device
        adb_command = f"adb -s {device_id} shell screencap -p"
        # device_id = "91220e34"  # Replace with your device ID
        # adb_command = f"adb -s {device_id} shell screencap -p"
        try:
            image_stream = subprocess.Popen(adb_command, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
            image_data = image_stream.stdout.read()
            image_bytes = io.BytesIO(image_data)
            image = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)
        except cv2.error as e:
            QMessageBox.warning(self, "警告", f"Error capturing image: {e}")
            # print(f"Error capturing image: {e}")
            return None
        return image

    def update_recent_saved_images_list(self, path):
        self.recent_saved_images.insert(0, path)
        if len(self.recent_saved_images) > self.max_recent_saved_images:
            self.recent_saved_images.pop()

        self.recent_saved_images_list.clear()
        for img_path in self.recent_saved_images:
            self.recent_saved_images_list.addItem(img_path)

    def show_saved_image(self, item):
        if not self.paused:
            QMessageBox.warning(self, "警告", "需要先暂停界面")
            return

        path = item.text()
        self.current_image_path = path
        self.img_save_histroy.setText(f"当前选择图片：{path.split('/')[-1]}")

        if self.current_image_path != self.last_saved_image_path:
            if self.is_changed:
                saved_image_confirm_dialog = self.confirm_dialog('提示', '是否保存当前标注？不保存将会丢失当前标注！')
                if saved_image_confirm_dialog:
                    # 判断路径是否存在
                    if os.path.exists(self.save_path_input.text()):
                        self.save_image()
                        self.clear_step()
                    else:
                        QMessageBox.warning(self, '提示', '保存路径不存在，请重新选择保存路径')
                        return
                else:
                    self.is_changed = False
                    # self.clear_step()
            # 切换图片时，会自动清除步骤列表选择
            self.is_selected_step_item = False
            self.current_selected_step_items_index = None
            # 初始化，不然切图会出现重复的框
            # self.init_list()
            self.clear_step()

            if os.path.exists(path):
                saved_image = cv2.imread(path)
                if saved_image is not None:
                    # 根据当前的缩放因子调整图像大小
                    height, width = saved_image.shape[:2]
                    new_width = int(width * self.scale_factor)
                    new_height = int(height * self.scale_factor)
                    resized_image = cv2.resize(saved_image, (new_width, new_height), interpolation=cv2.INTER_AREA)

                    qt_img = self.convert_cv2_image_to_pixmap(resized_image)
                    self.image_label.setPixmap(qt_img)
                    self.image_label.setScaledContents(False)
                    self.image_label.adjustSize()

                    # 将保存的图像存储在 last_saved_image 属性中，标记为最近保存的图像
                    self.last_saved_image = saved_image

                    # 展示历史图片的矩形框
                    self.txt_to_QRect(path)
                    self.show_the_same_as_scale_factor()
                    self.get_step_list()

                    # 初始化撤回和恢复操作的必要参数one_step_or_two，默认two_pos
                    for i in range(len(self.rect_info_list)):
                        self.image_label.one_step_or_two.append('two_pos')
                    self.last_saved_image_path = self.current_image_path

        self.viewing_saved_image = True

    def txt_to_QRect(self, image_path):
        img_width, img_height = get_image_size(image_path)
        img_formats = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'tiff', 'jfif', 'svg', 'ico']
        if image_path.split('.')[-1] in img_formats:
            # 初始化rects
            self.image_label.rects = []
            dirname = os.path.dirname(image_path)
            filename = os.path.basename(image_path)
            output_file = os.path.join(dirname, f"{filename.split('.')[0]}.txt")

            rect_info_list = read_txt(output_file, img_width, img_height)

            # 初始化self.txt_list用于历史图片的撤回和恢复
            self.txt_list = read_txt_to_str_list(output_file)

            for rect_info in rect_info_list:
                left_top = rect_info['left_top']
                right_bottom = rect_info['right_bottom']
                # 因为默认的图就是缩放到了0.25,所以这里要按比例乘以0.25
                rect = QRect(QPoint(left_top[0] * self.last_scale_factor, left_top[1] * self.last_scale_factor), QPoint(right_bottom[0] * self.last_scale_factor, right_bottom[1] * self.last_scale_factor))
                # 根据txt初始化rects画图点列表
                self.image_label.rects.append(rect)
            # 根据txt初始化步骤列表
            self.rect_info_list = rect_info_list

    # 可动态根据self.scale_factor调整矩形框位置
    # 让其和图片的缩放保持一致
    # 当点进行缩放前，需要先以上一个self.scale_factor还原为原本的大，再按照新的比例缩放
    def show_the_same_as_scale_factor(self):
        if self.last_scale_factor != self.scale_factor:
            for rect in self.image_label.rects:
                rect.setTopLeft(QPoint(rect.topLeft().x() / self.last_scale_factor * self.scale_factor, rect.topLeft().y() / self.last_scale_factor * self.scale_factor))
                rect.setBottomRight(QPoint(rect.bottomRight().x() / self.last_scale_factor * self.scale_factor, rect.bottomRight().y() / self.last_scale_factor * self.scale_factor))
            self.last_scale_factor = self.scale_factor

    def convert_cv2_image_to_pixmap(self, image):
        """Converts an OpenCV image to a QPixmap."""
        height, width, channel = image.shape
        bytes_per_line = channel * width
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, image)
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        return pixmap

    def load_saved_images_from_directory(self, directory):
        self.recent_saved_images = []
        self.recent_saved_images_list.clear()
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif')

        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            if os.path.isfile(full_path) and filename.lower().endswith(valid_extensions):
                if full_path not in self.recent_saved_images:
                    self.recent_saved_images.append(full_path)
                    self.recent_saved_images_list.addItem(full_path)

        # 如果超过最大历史记录限制，删除最早的记录
        while len(self.recent_saved_images) > self.max_recent_saved_images:
            self.recent_saved_images.pop(0)
            self.recent_saved_images_list.takeItem(0)

    def zoom_in(self):
        if self.scale_factor < self.max_scale_factor:
            self.scale_factor += self.scale_step
            self.apply_zoom()
            self.zoom_label.setText(f"缩放比例: {self.scale_factor:.2f}")
            self.show_the_same_as_scale_factor()

    def zoom_out(self):
        if self.scale_factor > self.min_scale_factor:
            self.scale_factor -= self.scale_step
            self.apply_zoom()
            self.zoom_label.setText(f"缩放比例: {self.scale_factor:.2f}")
            self.show_the_same_as_scale_factor()

    def apply_zoom(self):
        if self.paused:
            if self.viewing_saved_image:
                if self.last_saved_image is not None:
                    image = self.last_saved_image
                else:
                    return
            else:
                image = self.current_image
        else:
            image = self.current_image

        height, width, channel = image.shape
        new_width = int(width * self.scale_factor)
        new_height = int(height * self.scale_factor)

        # 确保新的尺寸不会超过原始尺寸
        new_width = min(new_width, width)
        new_height = min(new_height, height)

        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        qt_img = self.convert_cv2_image_to_pixmap(resized_image)
        self.image_label.setPixmap(qt_img)
        self.image_label.adjustSize()

    def change_image_scale(self):
        if self.current_image is None:
            return

        # Resize the image using OpenCV
        new_height = int(self.current_image.shape[0] * self.scale_factor)
        new_width = int(self.current_image.shape[1] * self.scale_factor)
        resized_image = cv2.resize(self.current_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

        # Convert the resized image to QPixmap
        height, width, channel = resized_image.shape
        bytes_per_line = 3 * width
        qimage = QImage(resized_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage.rgbSwapped())
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 如果要使用自定义窗口大小，请传入一个 QSize 对象，例如：QSize(800, 600)
    # 如果不传入参数，窗口将保持可调整大小
    window = MainWindow(window_size=QSize(1024, 768))

    window.show()
    sys.exit(app.exec())
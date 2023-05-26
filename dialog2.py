import sys
import time

import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, \
    QLineEdit, QLabel, QFileDialog, QWidget, QCompleter, QMessageBox

import yaml_manager
from config import timeout
from get_service_data import class_data, get_service_data
from imageviewer import ImageViewer
from tool import rectangle_info, normalization, get_image_size, find_keys_by_value


class CustomDialog(QDialog):
    def __init__(self, newyamldialog_instance=None, mousecustom_instance=None):
        super().__init__()

        if newyamldialog_instance:
            self.newyamldialog_instance = newyamldialog_instance
            self.mainwindow_instance = newyamldialog_instance.mousecustom_instance.mainwindow_instance
            self.mousecustom_instance = newyamldialog_instance.mousecustom_instance
        else:
            self.mainwindow_instance = mousecustom_instance.mainwindow_instance
            self.mousecustom_instance = mousecustom_instance
        self.class_data_values = []

        # 记录当前所选坐标
        self.start_point = self.mousecustom_instance.start_point
        self.end_point = self.mousecustom_instance.end_point

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('标签设置')
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()

        # # 对话框默认状态
        # self.v_layout = QVBoxLayout()

        # 父下拉框
        self.parent_selector = QComboBox()
        self.layout.addWidget(self.parent_selector)

        # 子下拉框
        self.class_selector = QComboBox()

        # 获取yaml对应的各个item
        # self.show_class_name()

        # 设置 QCompleter，关联下拉框，支持模糊搜索
        completer = QCompleter(self.class_data_values)
        completer.setCaseSensitivity(Qt.CaseInsensitive)  # 设置不区分大小写
        completer.setFilterMode(Qt.MatchContains)  # 设置模糊搜索模式
        self.class_selector.setCompleter(completer)
        self.layout.addWidget(self.class_selector)

        self.show_parent_name()
        self.parent_selector.currentTextChanged.connect(self.update_class_selector)
        # 添加按钮
        self.button_layout = QHBoxLayout()

        self.ok_button = QPushButton('确认')
        self.ok_button.clicked.connect(self.ok_button_clicked_for_server)

        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.show_input)
        self.add_button.setEnabled(False)

        self.modify_button = QPushButton("修改")
        self.modify_button.clicked.connect(self.show_modify_options)
        self.modify_button.setEnabled(False)

        self.show_image_button = QPushButton("案例", self)
        self.show_image_button.clicked.connect(self.show_images)

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.modify_button)
        self.button_layout.addWidget(self.show_image_button)


        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

        # 添加输入框
        self.input_line = QLineEdit()
        self.confirm_add_button = QPushButton("确定添加")
        self.confirm_add_button.clicked.connect(self.add_item)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_addition)

        self.confirm_modify_button = QPushButton("确认修改")
        self.confirm_modify_button.clicked.connect(self.modify_item)

    def show_input(self):
        self.switch_to_input()

    def switch_to_input(self):
        # 移除下拉列表和相关按钮
        self.layout.removeWidget(self.class_selector)
        self.class_selector.hide()
        self.button_layout.removeWidget(self.ok_button)
        self.ok_button.hide()
        self.button_layout.removeWidget(self.add_button)
        self.add_button.hide()
        self.button_layout.removeWidget(self.modify_button)
        self.modify_button.hide()
        self.button_layout.removeWidget(self.show_image_button)
        self.show_image_button.hide()

        # 添加输入框和相关按钮
        self.button_layout.addWidget(self.confirm_add_button)
        self.confirm_add_button.show()
        self.layout.insertWidget(0, self.input_line)
        self.input_line.show()
        self.input_line.clear()
        self.button_layout.addWidget(self.cancel_button)
        self.cancel_button.show()

    def switch_to_modify(self):
        # 移除下拉列表和相关按钮
        self.layout.removeWidget(self.class_selector)
        self.class_selector.hide()
        self.button_layout.removeWidget(self.ok_button)
        self.ok_button.hide()
        self.button_layout.removeWidget(self.add_button)
        self.add_button.hide()
        self.button_layout.removeWidget(self.modify_button)
        self.modify_button.hide()
        self.button_layout.removeWidget(self.show_image_button)
        self.show_image_button.hide()

        # 添加下拉列表和相关按钮
        self.button_layout.addWidget(self.confirm_modify_button)
        self.confirm_modify_button.show()
        self.layout.insertWidget(0, self.input_line)
        self.input_line.show()
        self.input_line.setText(self.class_selector.currentText())
        self.button_layout.addWidget(self.cancel_button)
        self.cancel_button.show()

    def show_modify_options(self):
        self.switch_to_modify()

    def add_item(self):
        new_item = self.input_line.text()
        if new_item:
            data = self.class_data
            if new_item in list(data['names'].values()):
                QMessageBox.warning(self, "提示", "此项已存在，请勿重复添加。")
            else:
                max_value = max(list(data['names'].keys()))
                data['names'][max_value + 1] = new_item

                yaml_path = self.mainwindow_instance.yaml_path_input.text()
                yaml_manager.yaml_write(yaml_path, data)
                time.sleep(1)
                self.show_class_name()
                QMessageBox.warning(self, "提示", "添加成功。")
                self.reset_dialog()
        else:
            QMessageBox.warning(self, "提示", "请输入一个有效的选项。")

    def show_images(self):
        parent = self.parent_selector.currentText()
        category = self.class_selector.currentText()
        self.image_viewer = ImageViewer(parent, category)
        self.image_viewer.show()
        self.hide()
        self.image_viewer.finished.connect(self.show)

    def cancel_addition(self):
        self.reset_dialog()

    def reset_dialog(self):
        self.input_line.hide()
        self.confirm_add_button.hide()
        self.cancel_button.hide()
        self.confirm_modify_button.hide()

        self.layout.insertWidget(0, self.class_selector)
        self.class_selector.show()
        self.button_layout.addWidget(self.ok_button)
        self.ok_button.show()
        self.button_layout.addWidget(self.add_button)
        self.add_button.show()
        self.button_layout.addWidget(self.modify_button)
        self.modify_button.show()
        self.button_layout.addWidget(self.show_image_button)
        self.show_image_button.show()

    def modify_item(self):
        # 需要处理修改时判断是否已存在的问题
        new_item = self.input_line.text()
        if new_item:
            data = self.class_data
            if new_item in list(data['names'].values()):
                QMessageBox.warning(self, "提示", "没有变更，无效修改。")
            else:
                index = self.class_selector.currentIndex()
                data['names'][index] = new_item

                yaml_path = self.mainwindow_instance.yaml_path_input.text()
                yaml_manager.yaml_write(yaml_path, data)
                time.sleep(1)
                self.show_class_name()
                QMessageBox.information(self, "提示", "修改成功。")
                self.reset_dialog()
        else:
            QMessageBox.warning(self, "提示", "请输入一个有效的选项。")

    # 非服务器获取类名方式，本地的yaml不含父类，所以可以直接获取
    def show_class_name(self):
        try:
            self.class_selector.clear()
            data = self.mainwindow_instance.class_data
            self.class_data = data
            self.class_data_values = list(data['names'].values())

            # print(self.class_data)
            if 'names' in data:
                for class_name_index in data['names'].keys():
                    self.class_selector.addItem(data['names'][class_name_index])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"读取YAML文件时出错: {e}")

    def update_class_selector(self, parent_name):
        self.class_selector.clear()
        data = class_data()
        data = data['data']
        class_list = data[parent_name]

        for class_name_index in range(len(class_list)):
            self.class_selector.addItem(class_list[class_name_index]['class_name'])

    # 获取服务器的类名方式
    def show_parent_name(self):

        # 创建一个 QTimer 实例
        self.timer = QTimer()
        self.timer.setSingleShot(True)  # 设置 QTimer 为一次性触发
        self.timer.timeout.connect(self.handle_timeout)  # 超时时调用 handle_timeout 函数
        self.timer.start(timeout * 1000)  # 设置超时时间为 5 秒

        try:
            self.parent_selector.clear()
            data = get_service_data()
            self.timer.stop()  # 如果请求成功，停止计时器
            try:
                if not self.class_selector.currentText():
                    data = data['data']
                    parent_list = list(data.keys())
                    class_list = data[parent_list[0]]
                    for class_name_index in range(len(class_list)):
                        self.class_selector.addItem(class_list[class_name_index]['class_name'])

                for parent in data.keys():
                    self.parent_selector.addItem(parent)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"读取服务器文件时出错: {e}")

        except requests.exceptions.Timeout:
            pass

    def handle_timeout(self):
        QMessageBox.warning(self, "警告", f"获取服务端数据超时")
        self.mainwindow_instance.server_status = False
        self.mainwindow_instance.yaml_path_input.setText("服务端状态：未连接")

    # 点击确认按钮时，获取服务器数据
    def ok_button_clicked_for_server(self):

        # 创建一个 QTimer 实例
        self.timer = QTimer()
        self.timer.setSingleShot(True)  # 设置 QTimer 为一次性触发
        self.timer.timeout.connect(self.handle_timeout)  # 超时时调用 handle_timeout 函数
        self.timer.start(timeout * 1000)  # 设置超时时间为 5 秒

        try:
            data = get_service_data()
            self.timer.stop()  # 如果请求成功，停止计时器
            current_parent_choice = self.parent_selector.currentText()
            current_choice = self.class_selector.currentText()
            for item_num in range(len(data[current_parent_choice])):
                if data[current_parent_choice][item_num]['class_name'] == current_choice:
                    self.class_id = data[current_parent_choice][item_num]['class_id']
                    break

            if self.class_id is not None:
                start_point = self.mousecustom_instance.start_point
                end_point = self.mousecustom_instance.end_point

                if start_point is None or end_point is None:
                    start_point = self.start_point
                    end_point = self.end_point

                start_point_to_xy = (start_point.x() / self.mainwindow_instance.scale_factor,
                                     start_point.y() / self.mainwindow_instance.scale_factor)
                end_point_to_xy = (end_point.x() / self.mainwindow_instance.scale_factor,
                                   end_point.y() / self.mainwindow_instance.scale_factor)

                if self.mainwindow_instance.viewing_saved_image:
                    try:
                        img_width, img_height = get_image_size(self.mainwindow_instance.current_image_path)
                    except Exception as e:
                        QMessageBox.warning(self, "警告",
                                            f"获取图像 {self.mainwindow_instance.current_image_path} 长宽信息出错: {e}")
                else:
                    img_width = self.mainwindow_instance.img_width
                    img_height = self.mainwindow_instance.img_height

                rect_info = rectangle_info(start_point_to_xy, end_point_to_xy, class_id=self.class_id)

                # 写入归一化，需要区分是否为旧图，旧图获取图像长宽的方式和实时获取的方式不一样
                annotation_str = normalization(rect_info, img_width, img_height)

                self.mainwindow_instance.ok_count += 1
                self.mainwindow_instance.txt_list.append(annotation_str)
                self.mainwindow_instance.rect_info_list.append(rect_info)
                # self.mainwindow_instance.rect_info_list_copy = copy.copy(self.mainwindow_instance.rect_info_list)
                items = [rect_info['class_id'], rect_info['center_point'], rect_info['width'], rect_info['length']]
                self.mainwindow_instance.step_dict[self.mainwindow_instance.ok_count] = items
                self.mainwindow_instance.get_step_list()

                self.mousecustom_instance.is_saved = True
                # 判断是否在旧图下点过确认按钮，点过的话则存在改动
                if self.mainwindow_instance.viewing_saved_image:
                    self.mainwindow_instance.is_changed = True
                    self.mainwindow_instance.is_image_saved = False
                self.close()
            else:
                QMessageBox.warning(self, "警告", "该类别不存在。")
        except requests.exceptions.Timeout:
            pass

    # 弹窗的确定按钮local版
    def ok_button_clicked(self):
        current_choice = self.class_selector.currentText()
        current_index = self.class_selector.currentIndex()
        start_point = self.mousecustom_instance.start_point
        end_point = self.mousecustom_instance.end_point

        if start_point is None or end_point is None:
            start_point = self.start_point
            end_point = self.end_point

        start_point_to_xy = (start_point.x()/self.mainwindow_instance.scale_factor, start_point.y()/self.mainwindow_instance.scale_factor)
        end_point_to_xy = (end_point.x()/self.mainwindow_instance.scale_factor, end_point.y()/self.mainwindow_instance.scale_factor)

        if self.mainwindow_instance.viewing_saved_image:
            try:
                img_width, img_height = get_image_size(self.mainwindow_instance.current_image_path)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"获取图像 {self.mainwindow_instance.current_image_path} 长宽信息出错: {e}")
        else:
            img_width = self.mainwindow_instance.img_width
            img_height = self.mainwindow_instance.img_height

        print(f"点击okbutton h:{img_height} w:{img_width}")
        rect_info = rectangle_info(start_point_to_xy, end_point_to_xy, class_id=current_index)

        # 写入归一化，需要区分是否为旧图，旧图获取图像长宽的方式和实时获取的方式不一样
        annotation_str = normalization(rect_info, img_width, img_height)

        # 最后点击保存才会写入到txt里面
        if current_index >= 0:
            self.mainwindow_instance.ok_count += 1
            self.mainwindow_instance.txt_list.append(annotation_str)
            self.mainwindow_instance.rect_info_list.append(rect_info)
            # self.mainwindow_instance.rect_info_list_copy = copy.copy(self.mainwindow_instance.rect_info_list)
            items = [rect_info['class_id'], rect_info['center_point'], rect_info['width'], rect_info['length']]
            self.mainwindow_instance.step_dict[self.mainwindow_instance.ok_count] = items
            self.mainwindow_instance.get_step_list()

        self.mousecustom_instance.is_saved = True
        # 判断是否在旧图下点过确认按钮，点过的话则存在改动
        if self.mainwindow_instance.viewing_saved_image:
            self.mainwindow_instance.is_changed = True
            self.mainwindow_instance.is_image_saved = False
        self.close()

    def closeEvent(self, event):
        if not self.mousecustom_instance.is_saved:
            # 当以两点画矩形时，因为第二点的点击操作会触发对话框，
            if self.mousecustom_instance.rects:
                # 和撤回逻辑类似，如果是两点画矩形，那么就要把两个点都pop掉
                if self.mousecustom_instance.one_step_or_two[-1] == 'one_pos':
                    self.mousecustom_instance.rects.pop()
                    self.mousecustom_instance.rects.pop()
                    self.mousecustom_instance.one_step_or_two.pop()
                    self.mousecustom_instance.one_step_or_two.pop()
                else:
                    self.mousecustom_instance.rects.pop()
                    self.mousecustom_instance.one_step_or_two.pop()

        self.mousecustom_instance.is_saved = False

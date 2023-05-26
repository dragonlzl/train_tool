import copy
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, \
    QLineEdit, QLabel, QFileDialog, QWidget, QCompleter, QMessageBox

import yaml_manager
from tool import rectangle_info, normalization


class CustomDialog(QDialog):
    def __init__(self, mousecustom_instance):
        super().__init__()

        self.mainwindow_instance = mousecustom_instance.mainwindow_instance
        self.mousecustom_instance = mousecustom_instance
        self.class_data_values = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('标签设置')
        self.layout = QVBoxLayout()

        # 对话框默认状态
        self.v_layout = QVBoxLayout()
        # 下拉框
        self.class_selector = QComboBox()
        # 获取yaml对应的各个item
        self.show_class_name()
        # self.v_layout.addWidget(self.class_selector)

        # 设置 QCompleter，关联下拉框，支持模糊搜索
        completer = QCompleter(self.class_data_values)
        completer.setCaseSensitivity(Qt.CaseInsensitive)  # 设置不区分大小写
        completer.setFilterMode(Qt.MatchContains)  # 设置模糊搜索模式

        self.class_selector.setCompleter(completer)

        self.v_layout.addWidget(self.class_selector)

        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton('确认')
        self.ok_button.clicked.connect(self.ok_button_clicked)

        self.change_button = QPushButton('修改')

        self.add_button = QPushButton('添加')

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.change_button)
        self.button_layout.addWidget(self.add_button)

        self.v_layout.addLayout(self.button_layout)
        self.return_button = QPushButton('返回')
        # self.class_selector = QComboBox()
        self.input_field = QLineEdit()

        # self.button2.clicked.connect(self.show_input_field)
        self.return_button.clicked.connect(self.return_to_default)

        self.layout.addLayout(self.v_layout)
        # self.layout.addWidget(self.dropdown)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.return_button)

        self.return_to_default()
        self.setLayout(self.layout)

    def show_class_selector(self):
        self.class_selector.show()
        self.input_field.hide()
        self.return_button.show()

    def show_input_field(self):
        # self.dropdown.hide()
        self.input_field.show()
        self.return_button.show()

    def return_to_default(self):
        # self.dropdown.hide()
        self.input_field.hide()
        self.return_button.hide()

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
            # print(f"读取YAML文件时出错: {e}")

    # 弹窗的确定按钮
    def ok_button_clicked(self):
        current_choice = self.class_selector.currentText()
        current_index = self.class_selector.currentIndex()
        start_point = self.mousecustom_instance.start_point
        end_point = self.mousecustom_instance.end_point

        start_point_to_xy = (start_point.x()/self.mainwindow_instance.scale_factor, start_point.y()/self.mainwindow_instance.scale_factor)
        end_point_to_xy = (end_point.x()/self.mainwindow_instance.scale_factor, end_point.y()/self.mainwindow_instance.scale_factor)

        # 高大于宽就是竖屏
        if self.mainwindow_instance.current_height > self.mainwindow_instance.current_width:
            screen_orientation = 'portrait'
        else:
            screen_orientation = 'landscape'
        rect_info = rectangle_info(start_point_to_xy, end_point_to_xy, class_id=current_index, screen_orientation=screen_orientation)

        img_width = self.mainwindow_instance.img_width
        img_height = self.mainwindow_instance.img_height

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
            self.mainwindow_instance.is_image_saved = False
            self.mainwindow_instance.is_changed = True
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

# test MainWindow
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("YAML文件选择器")
        self.setGeometry(300, 300, 400, 150)

        layout = QVBoxLayout()

        self.file_input = QLineEdit(self)
        layout.addWidget(self.file_input)

        self.select_button = QPushButton("选择文件", self)
        self.select_button.clicked.connect(self.choose_file)
        layout.addWidget(self.select_button)

        self.button = QPushButton('打开对话框', self)
        self.button.clicked.connect(self.open_dialog)
        self.button.move(100, 80)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def open_dialog(self):
        self.dialog = CustomDialog(self)
        self.dialog.exec_()

    def choose_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "YAML文件 (*.yaml);;所有文件 (*)", options=options)

        if file:
            self.file_input.setText(file)
            self.load_classes(file)
            # print(self.class_data)

    def load_classes(self, yaml_path):
        try:
            self.class_data = yaml_manager.yaml_read(yaml_path)
        except Exception as e:
            # print(f"读取YAML文件时出错: {e}")
            QMessageBox.warning(self, "警告", f"读取YAML文件时出错: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

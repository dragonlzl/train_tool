# 使用pyqt5实现一个对话框
# 对话框依次展示一个yaml文件名输入框，路径输入框、路径选择按钮，类名输入框、确认按钮、取消按钮
# 点击确认时，会检查文件名输入框是否为空，如果为空，弹出提示框，提示用户输入文件名
# 点击确认时，会检查路径输入框是否为空，如果为空，弹出提示框，提示用户输入或选择路径
# 点击确认时，会检查类名输入框是否为空，如果为空，弹出提示框，提示用户输入类名
# 点击确认时，如果检查全部通过，则输出该yaml文件的路径和类名
# 点击取消时，关闭对话框，并打印出close
import os.path
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QFileDialog, QMessageBox

from dialog2 import CustomDialog
from yaml_manager import yaml_read, yaml_write


class NewYamlDialog(QDialog):
    def __init__(self, mousecustom_instance):
        super().__init__()

        self.mousecustom_instance = mousecustom_instance
        self.mainwindow_instance = mousecustom_instance.mainwindow_instance
        self.init_ui()
        self.show()

    def init_ui(self):
        self.setWindowTitle("新建YAML")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # self.resize(400, 150)

        layout = QVBoxLayout()

        yaml_name_layout = QHBoxLayout()
        self.yaml_name_label = QLabel("文件名字：", self)
        self.file_input = QLineEdit(self)
        yaml_name_layout.addWidget(self.yaml_name_label)
        yaml_name_layout.addWidget(self.file_input)
        layout.addLayout(yaml_name_layout)

        yaml_path_layout = QHBoxLayout()
        self.yaml_name_label = QLabel("保存目录：", self)
        self.path_input = QLineEdit(self)
        yaml_path_layout.addWidget(self.yaml_name_label)
        yaml_path_layout.addWidget(self.path_input)
        layout.addLayout(yaml_path_layout)

        self.select_button = QPushButton("选择路径", self)
        self.select_button.clicked.connect(self.choose_path)
        layout.addWidget(self.select_button)

        class_layout = QHBoxLayout()
        self.class_label = QLabel("类别名字：", self)
        self.class_input = QLineEdit(self)
        class_layout.addWidget(self.class_label)
        class_layout.addWidget(self.class_input)
        layout.addLayout(class_layout)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("确认", self)
        self.confirm_button.clicked.connect(self.confirm)
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self.cancel)
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    # 点击选择路径按钮时，弹出文件保存的文件夹选择框
    def choose_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        save_directory = QFileDialog.getExistingDirectory(self, "选择保存路径", "", options=options)
        self.path_input.setText(save_directory)

    def confirm(self):
        file_name = self.file_input.text()
        path = self.path_input.text()
        class_name = self.class_input.text()

        if not file_name:
            QMessageBox.warning(self, "警告", "请输入文件名")
            return
        if not path:
            QMessageBox.warning(self, "警告", "请输入路径")
            return
        if not class_name:
            QMessageBox.warning(self, "警告", "请输入类名")
            return

        if os.path.exists(path):
            # 获取脚本运行目录
            root = os.path.dirname(os.path.abspath(__file__))
            self.yaml_path = os.path.join(path, f"{file_name}.yaml")
            yaml_template = os.path.join(root, "template.yaml")

            if os.path.exists(self.yaml_path):
                QMessageBox.warning(self, "警告", "文件已存在")
                return
        else:
            QMessageBox.warning(self, "警告", "路径不存在")
            return

        # 获取模版数据
        config = yaml_read(yaml_template)
        config['names'][0] = class_name
        yaml_write(self.yaml_path, config)
        QMessageBox.information(self, "提示", "创建成功")
        self.mainwindow_instance.yaml_path_input.setText(self.yaml_path)
        self.mainwindow_instance.load_classes(self.yaml_path)
        self.close()
        self.open_dialog()

    def cancel(self):
        self.close()

    def closeEvent(self, event):
        self.mainwindow_instance.clear_step()
        self.close()

    def open_dialog(self):
        self.dialog = CustomDialog(newyamldialog_instance=self)
        self.dialog.exec_()

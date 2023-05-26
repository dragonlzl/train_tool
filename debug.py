import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QComboBox, QPushButton, QLineEdit, QHBoxLayout, QMessageBox


class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        # 设置窗口标题
        self.setWindowTitle("Custom Dialog")

        # 设置布局
        self.layout = QVBoxLayout()

        # 添加下拉列表
        self.combobox = QComboBox()
        self.combobox.addItems(["Item 1", "Item 2", "Item 3"])
        self.layout.addWidget(self.combobox)

        # 添加按钮
        self.buttons_layout = QHBoxLayout()

        self.confirm_button = QPushButton("确定")
        self.confirm_button.clicked.connect(self.confirm_selection)
        self.buttons_layout.addWidget(self.confirm_button)

        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.show_input)
        self.buttons_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.show_delete_options)
        self.buttons_layout.addWidget(self.delete_button)

        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)

        # 添加输入框
        self.input_line = QLineEdit()
        self.confirm_add_button = QPushButton("确定添加")
        self.confirm_add_button.clicked.connect(self.add_item)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_addition)

        self.confirm_delete_button = QPushButton("确认删除")
        self.confirm_delete_button.clicked.connect(self.delete_item)

    def confirm_selection(self):
        print(f"当前所选项：{self.combobox.currentText()}")

    def show_input(self):
        self.switch_to_input()

    def switch_to_input(self):
        # 移除下拉列表和相关按钮
        self.layout.removeWidget(self.combobox)
        self.combobox.hide()
        self.buttons_layout.removeWidget(self.add_button)
        self.add_button.hide()
        self.buttons_layout.removeWidget(self.delete_button)
        self.delete_button.hide()
        self.buttons_layout.removeWidget(self.confirm_button)
        self.confirm_button.hide()

        # 添加输入框和相关按钮
        self.layout.insertWidget(0, self.input_line)
        self.input_line.show()
        self.buttons_layout.addWidget(self.confirm_add_button)
        self.confirm_add_button.show()
        self.buttons_layout.addWidget(self.cancel_button)
        self.cancel_button.show()

    def show_delete_options(self):
        self.switch_to_delete()

    def switch_to_delete(self):
        # 移除下拉列表和相关按钮
        self.layout.removeWidget(self.combobox)
        self.combobox.hide()
        self.buttons_layout.removeWidget(self.add_button)
        self.add_button.hide()
        self.buttons_layout.removeWidget(self.delete_button)
        self.delete_button.hide()
        self.buttons_layout.removeWidget(self.confirm_button)
        self.confirm_button.hide()

        # 添加下拉列表和相关按钮
        self.layout.insertWidget(0, self.combobox)
        self.combobox.show()
        self.buttons_layout.addWidget(self.confirm_delete_button)
        self.confirm_delete_button.show()
        self.buttons_layout.addWidget(self.cancel_button)
        self.cancel_button.show()

    def add_item(self):
        new_item = self.input_line.text()
        if new_item:
            if self.combobox.findText(new_item) == -1:
                self.combobox.addItem(new_item)
                self.reset_dialog()
            else:
                QMessageBox.warning(self, "提示", "此项已存在，请勿重复添加。")
        else:
            QMessageBox.warning(self, "提示", "请输入一个有效的选项。")

    def cancel_addition(self):
        self.reset_dialog()

    def reset_dialog(self):
        self.input_line.hide()
        self.confirm_add_button.hide()
        self.cancel_button.hide()
        self.confirm_delete_button.hide()

        self.layout.insertWidget(0, self.combobox)
        self.combobox.show()
        self.buttons_layout.addWidget(self.add_button)
        self.add_button.show()
        self.buttons_layout.addWidget(self.delete_button)
        self.delete_button.show()
        self.buttons_layout.addWidget(self.confirm_button)
        self.confirm_button.show()

    def delete_item(self):
        current_item = self.combobox.currentText()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除 {current_item} 吗？",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            index = self.combobox.currentIndex()
            self.combobox.removeItem(index)
            self.reset_dialog()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = CustomDialog()
    dialog.exec()

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        # 设置窗口标题
        self.setWindowTitle("Custom Dialog")

        # 设置布局
        self.layout = QVBoxLayout()

        # 添加组合框（下拉列表）
        self.combobox = QComboBox()
        self.combobox.addItems(["Option 1", "Option 2", "Option 3"])
        self.layout.addWidget(self.combobox)

        # 添加输入框
        self.input_line = QLineEdit()
        self.layout.addWidget(self.input_line)
        self.input_line.hide()

        # 添加按钮
        self.buttons_layout = QHBoxLayout()
        self.confirm_button = QPushButton("确定")
        self.confirm_button.clicked.connect(self.confirm_selection)
        self.buttons_layout.addWidget(self.confirm_button)

        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.prepare_add_item)
        self.buttons_layout.addWidget(self.add_button)

        self.modify_button = QPushButton("修改")
        self.modify_button.clicked.connect(self.prepare_modify_item)
        self.buttons_layout.addWidget(self.modify_button)

        self.confirm_modify_button = QPushButton("确认修改")
        self.confirm_modify_button.clicked.connect(self.modify_item)
        self.buttons_layout.addWidget(self.confirm_modify_button)
        self.confirm_modify_button.hide()

        self.confirm_add_button = QPushButton("确定添加")
        self.confirm_add_button.clicked.connect(self.add_item)
        self.buttons_layout.addWidget(self.confirm_add_button)
        self.confirm_add_button.hide()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_addition)
        self.buttons_layout.addWidget(self.cancel_button)
        self.cancel_button.hide()

        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)

    def confirm_selection(self):
        print(f"选中的项: {self.combobox.currentText()}")

    def prepare_add_item(self):
        self.combobox.hide()
        self.add_button.hide()
        self.modify_button.hide()
        self.confirm_button.hide()

        self.input_line.show()
        self.confirm_add_button.show()
        self.cancel_button.show()

    def prepare_modify_item(self):
        self.combobox.hide()
        self.add_button.hide()
        self.modify_button.hide()
        self.confirm_button.hide()

        self.input_line.show()
        self.input_line.setText(self.combobox.currentText())
        self.confirm_modify_button.show()
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

    def modify_item(self):
        new_item = self.input_line.text()
        if new_item:
            index = self.combobox.currentIndex()
            self.combobox.removeItem(index)
            self.combobox.insertItem(index, new_item)
            self.combobox.setCurrentIndex(index)
            QMessageBox.information(self, "提示", "修改成功。")
            self.reset_dialog()
        else:
            QMessageBox.warning(self, "提示", "请输入一个有效的选项。")

    def cancel_addition(self):
        self.reset_dialog()

    def reset_dialog(self):
        self.input_line.hide()
        self.confirm_add_button.hide()
        self.confirm_modify_button.hide()
        self.cancel_button.hide()

        self.combobox.show()
        self.add_button.show()
        self.modify_button.show()
        self.confirm_button.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = CustomDialog()
    dialog.exec()


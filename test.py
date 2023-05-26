import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QPushButton

class ListWidgetExample(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('QListWidget 示例')
        self.setGeometry(100, 100, 300, 200)

        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        items = ['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5']
        self.list_widget.addItems(items)
        self.layout.addWidget(self.list_widget)

        self.delete_button = QPushButton('删除选定项')
        self.delete_button.clicked.connect(self.delete_selected_item)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

    def delete_selected_item(self):
        selected_items = self.list_widget.selectedItems()

        for item in selected_items:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

app = QApplication(sys.argv)
example = ListWidgetExample()
example.show()
sys.exit(app.exec_())

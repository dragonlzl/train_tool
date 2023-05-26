from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap

class CustomQDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Custom QDialog with QLabel")

        self.label = QLabel(self)
        pixmap = QPixmap("/Users/linzhenlong/PycharmProjects/train_tool/imgtest/2023_04_20_14_40_20.png")
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(255, 0, 0), 3, Qt.SolidLine))

        rect = QRect(self.label.pos(), self.label.size())
        painter.drawRect(rect)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dlg = CustomQDialog()
    dlg.show()
    sys.exit(app.exec_())

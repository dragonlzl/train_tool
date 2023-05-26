import os
import sys

import typing
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from uicomponent import Ui_drawing_widget1
# import uicomponent.Ui_drawing_widget1

class ScreenWidget(QWidget):

    save_signal_data = pyqtSignal(QPixmap)  # 保存图片信号
    callout_box_info = pyqtSignal(tuple, tuple)    # 获取标注框内容信号

    def __init__(self, parent: typing.Optional['QWidget'] = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("screen")
        self.showFullScreen()
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 截屏并获取屏幕信息
        self.screen = QApplication.primaryScreen().grabWindow(QApplication.desktop().winId())
        self.screen_size = self.screen.rect().size()
        self.screen_rect = self.get_rect_f(self.screen.rect())
        # 获取屏幕左上角，左下角，右上角，右下角的信息
        self.screen_top_left = self.screen_rect.topLeft()
        self.screen_bottom_left = self.screen_rect.bottomLeft()
        self.screen_top_right = self.screen_rect.topRight()
        self.screen_bottom_right = self.screen_rect.bottomRight()

        # 设置上下左右的限制
        self.screen_left = self.screen_rect.left()
        self.screen_right = self.screen_rect.right()
        self.screen_top = self.screen_rect.top()
        self.screen_bottom = self.screen_rect.bottom()

        # 设置屏幕截图为窗口背景
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(self.screen))
        self.setPalette(palette)

        # 调节器层
        self.adjustment_original = QPixmap(self.screen_size)
        self.adjustment_original.fill(QColor(0, 0, 0, 64))
        self.adjustment = QPixmap()  # 调节器    

        # 画布层
        self.canvas_original = QPixmap(self.screen_size)  
        self.canvas_original.fill(Qt.transparent)
        # 保存已经画好的图案
        self.canvas_saved = self.canvas_original.copy()  
        # 画布
        self.canvas = QPixmap()  
        self.canvas_rect = None
        self.canvas_rect_lists: typing.List[QRect] = []
        self.canvas_rect_lists_copy: typing.List[QRect] = []


        self.output = QPixmap()
        # 当前功能状态
        self.is_masking = False
        self.has_mask = False
        self.is_moving = False
        self.is_adjusting = False
        self.is_drawing = False
        self.has_pattern = False
        self.mouse_pos = ''
        self.is_shifting = False
        self.is_tagging = False

        # 蒙版 和 蒙版信息
        self.mask_rect = QRectF()
        self.mask_rect_backup = QRectF()

        # 以下 16 个变量随self.mask_rect变化而变化
        self.mask_top_left = QPoint()
        self.mask_bottom_left = QPoint()
        self.mask_top_right = QPoint()
        self.mask_bottom_right = QPoint()
        self.mask_top_mid = QPoint()
        self.mask_bottom_mid = QPoint()
        self.mask_left_mid = QPoint()
        self.mask_right_mid = QPoint()

        self.rect_top_left = QRectF()
        self.rect_bottom_left = QRectF()
        self.rect_top_right = QRectF()
        self.rect_bottom_right = QRectF()
        self.rect_top = QRectF()
        self.rect_bottom = QRectF()
        self.rect_left = QRectF()
        self.rect_right = QRectF()

        self.adjustment_line_width = 2
        self.adjustment_white_dot_radius = 6
        self.adjustment_blue_dot_radius = 4
        self.blue = QColor(30, 120, 255)
        # 设置鼠标样式: 十字
        self.setCursor(Qt.CrossCursor)  
        self.setMouseTracking(True)

        # 鼠标事件点
        self.start = QPoint()
        self.end = QPoint()

        # 工具视图
        self.tools_form = Ui_drawing_widget1.Ui_Form()
        self.tools_form.is_tagging_signal_data.connect(self.change_dimension_status_clicked)
        self.tools_form.cancel_event.connect(self.cancel_step_clicked)
        self.tools_form.save_event.connect(self.save_clicked)
        self.tools_form.show()
        self.tools_form.setVisible(False)

    def change_dimension_status_clicked(self, status: bool):
        self.is_tagging = status
        self.update()

    def cancel_step_clicked(self):
        if len(self.canvas_rect_lists) < 1:
            return
        self.canvas_rect_lists = self.canvas_rect_lists[0:len(self.canvas_rect_lists) - 1]
        self.update()
    
    def save_clicked(self):
        if len(self.canvas_rect_lists) < 1:
            reply = QMessageBox.question(self, '', "当前还未对图片进行标注，是否保存？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply ==  QMessageBox.No:
                return
        self.save()
        self.tools_form.close()
        self.close()
        
    def create_rect(self):
        """绘制矩形"""
        rect = QRectF(self.start, self.end)
        if self.is_shifting:
            x = rect.x()
            y = rect.y()
            w = rect.width()
            h = rect.height()
            abs_w = abs(w)
            abs_h = abs(h)
            w_is_longer = True if abs_w > abs_h else False
            if w > 0:
                if h > 0:
                    end = QPoint(x + abs_w, y + abs_w) if w_is_longer else QPoint(x + abs_h, y + abs_h)
                else:
                    end = QPoint(x + abs_w, y - abs_w) if w_is_longer else QPoint(x + abs_h, y - abs_h)  
            else:
                 if h > 0:
                    end = QPoint(x - abs_w, y + abs_w) if w_is_longer else QPoint(x - abs_h, y + abs_h)
                 else:
                    end = QPoint(x - abs_w, y - abs_w) if w_is_longer else QPoint(x - abs_h, y - abs_h)

            rect = QRectF(self.start, end)

        self.mask_rect = QRectF(
            rect.x() + min(rect.width(), 0),
            rect.y() + min(rect.height(), 0),
            abs(rect.width()),
            abs(rect.height())
        ) 

        # 防止框选区域超出屏幕
        if self.is_shifting:
            self.limit_box_selection_area()

        self.update_mask_info()
        self.update()

    def limit_box_selection_area(self):
        """限制框选区域，防止超出屏幕"""
        vector = self.end - self.start
        vX = vector.x()
        vY = vector.y()
        resStart = self.mask_rect.topLeft()
        resEnd = self.mask_rect.bottomRight()
        mLeft = self.mask_rect.left()
        mRight = self.mask_rect.right()
        mTop = self.mask_rect.top()
        mBottom = self.mask_rect.bottom()
        # w < h
        if self.mask_rect.left() <= self.screen_left:
            newW = mRight - self.screen_left
            if vY > 0:
                resStart = QPoint(self.screen_left, mTop)
                resEnd = resStart + QPoint(newW, newW)
            else:
                resStart = resEnd + QPoint(-newW, -newW)
        elif self.mask_rect.right() >= self.screen_right:
            newW = self.screen_right - mLeft
            if vY > 0:
                resEnd = resStart + QPoint(newW, newW)
            else:
                resEnd = QPoint(self.screen_right, mBottom)
                resStart = resEnd + QPoint(-newW, -newW)
        # w > h
        elif self.mask_rect.top() <= self.screen_top:
            newW = mBottom - self.screen_top
            if vX > 0:
                resStart = QPoint(mLeft, self.screen_top)
                resEnd = resStart + QPoint(newW, newW)
            else:
                resStart = resEnd + QPoint(-newW, -newW)
        elif self.mask_rect.bottom() >= self.screen_bottom:
            newW = self.screen_bottom - mTop
            if vX > 0:
                resEnd = resStart + QPoint(newW, newW)
            else:
                resEnd = QPoint(mRight, self.screen_bottom)
                resStart = resEnd + QPoint(-newW, -newW)
        self.mask_rect = QRectF(resStart, resEnd)

    def on_move(self):
        mStart = self.mask_rect_backup.topLeft()
        mStartX = mStart.x()
        mStartY = mStart.y()
        mEnd = self.mask_rect_backup.bottomRight()
        mEndX = mEnd.x()
        mEndY = mEnd.y()
        mWidth = self.mask_rect_backup.width()
        mHeight = self.mask_rect_backup.height()
        mWHPoint = QPoint(mWidth, mHeight)
        vector = self.end - self.start
        vX = vector.x()
        vY = vector.y()

        resStart = mStart + vector
        resStartX = resStart.x()
        resStartY = resStart.y()
        resEnd = mEnd + vector
        resEndX = resEnd.x()
        resEndY = resEnd.y()

        if resStartX <= self.screen_left and resStartY <= self.screen_top:
            resStart = self.screen_top_left
            resEnd = resStart + mWHPoint
        elif resEndX >= self.screen_right and resEndY >= self.screen_bottom:
            resEnd = self.screen_bottom_right
            resStart = resEnd - mWHPoint
        elif resStartX <= self.screen_left and resEndY >= self.screen_bottom:
            resStart = QPoint(self.screen_left, self.screen_bottom - mHeight)
            resEnd = resStart + mWHPoint
        elif resEndX >= self.screen_right and resStartY <= self.screen_top:
            resStart = QPoint(self.screen_right - mWidth, self.screen_top)
            resEnd = resStart + mWHPoint
        elif resStartX <= self.screen_left:
            resStart = QPoint(self.screen_left, mStartY + vY)
            resEnd = resStart + mWHPoint
        elif resStartY <= self.screen_top:
            resStart = QPoint(mStartX + vX, self.screen_top)
            resEnd = resStart + mWHPoint
        elif resEndX >= self.screen_right:
            resEnd = QPoint(self.screen_right, mEndY + vY)
            resStart = resEnd - mWHPoint
        elif resEndY >= self.screen_bottom:
            resEnd = QPoint(mEndX + vX, self.screen_bottom)
            resStart = resEnd - mWHPoint
        self.mask_rect = self.normalize_rect(QRectF(resStart, resEnd))
        self.update_mask_info()
        self.update()

    def on_adjust(self):
        mRect = self.mask_rect_backup
        mStart = mRect.topLeft()
        mStartX = mStart.x()
        mStartY = mStart.y()
        mEnd = mRect.bottomRight()
        mEndX = mEnd.x()
        mEndY = mEnd.y()
        resStart = mStart
        resEnd = mEnd
        if not self.is_shifting:

            if self.mouse_pos == 'TL':
                resStart = self.end
            elif self.mouse_pos == 'BL':
                resStart = QPoint(self.end.x(), mStartY)
                resEnd = QPoint(mEndX, self.end.y())
            elif self.mouse_pos == 'TR':
                resStart = QPoint(mStartX, self.end.y())
                resEnd = QPoint(self.end.x(), mEndY)
            elif self.mouse_pos == 'BR':
                resEnd = self.end
            elif self.mouse_pos == 'T':
                resStart = QPoint(mStartX, self.end.y())
            elif self.mouse_pos == 'B':
                resEnd = QPoint(mEndX, self.end.y())
            elif self.mouse_pos == 'L':
                resStart = QPoint(self.end.x(), mStartY)
            elif self.mouse_pos == 'R':
                resEnd = QPoint(self.end.x(), mEndY)
        else:
            if self.mouse_pos == 'T':
                resStart = QPoint(mStartX, self.end.y())
                newW = mEndY - self.end.y()
                resEnd = resStart + QPoint(newW, newW)
            elif self.mouse_pos == 'B':
                newW = self.end.y() - mStartY
                resEnd = resStart + QPoint(newW, newW)
            elif self.mouse_pos == 'L':
                resStart = QPoint(self.end.x(), mStartY)
                newW = mEndX - self.end.x()
                resEnd = resStart + QPoint(newW, newW)
            elif self.mouse_pos == 'R':
                newW = self.end.x() - mStartX
                resEnd = resStart + QPoint(newW, newW)
            elif self.mouse_pos == 'TL':
                newW = mEndX - self.end.x()
                newH = mEndY - self.end.y()
                newW = newW if newW > newH else newH
                resStart = resEnd + QPoint(-newW, -newW)
            elif self.mouse_pos == 'BR':
                newW = self.end.x() - mStartX
                newH = self.end.y() - mStartY
                newW = newW if newW > newH else newH
                resEnd = resStart + QPoint(newW, newW)
            elif self.mouse_pos == 'TR':
                newW = self.end.x() - mStartX
                newH = mEndY - self.end.y()
                newW = newW if newW > newH else newH
                resStart = mRect.bottomLeft()
                resEnd = resStart + QPoint(newW, -newW)
            elif self.mouse_pos == 'BL':
                newW = mEndX - self.end.x()
                newH = self.end.y() - mStartY
                newW = newW if newW > newH else newH
                resStart = mRect.topRight()
                resEnd = resStart + QPoint(-newW, newW)

        self.mask_rect = self.normalize_rect(QRectF(resStart, resEnd))

        self.limit_box_selection_area()

        self.update_mask_info()
        self.update()        

    def on_tagging(self):
        x, y = self.start.x(), self.start.y()
        w, h = self.end.x() - x,  self.end.y() - y
        self.canvas_rect = QRect(x, y, w, h)
        self.update()

    def mousePressEvent(self, mouse_event: QMouseEvent) -> None:
        if mouse_event.button() == Qt.LeftButton:
            self.start = mouse_event.pos()
            self.end = self.start
            if self.has_mask:
                self.mask_rect_backup = self.mask_rect
                if self.mouse_pos == 'mask':
                    self.is_moving = True
                elif self.is_tagging:
                    self.is_drawing = True
                else:
                    self.is_adjusting =True
            else:
                self.is_masking = True
    
    def mouseReleaseEvent(self, mouse_event: QMouseEvent) -> None:
        if mouse_event.button() == Qt.LeftButton:
            if not self.tools_form.isVisible():
                self.tools_form.setVisible(True)
            self.tools_form.move(int(self.screen_rect.right()/2), int(self.screen_rect.y()+30))
            self.is_masking = False
            self.is_moving = False
            self.is_adjusting = False
            self.is_drawing = False
            if self.receivers(self.callout_box_info) > 0:
                self.callout_box_info.emit(
                    (
                        self.canvas.width(), 
                        self.canvas.height()
                    ),
                    (
                        self.canvas_rect.x() + int(self.canvas_rect.width()/2),
                        self.canvas_rect.y() + int(self.canvas_rect.height()/2),
                        self.canvas_rect.width(),
                        self.canvas_rect.height()
                    )
                )
            if self.canvas_rect:
                self.canvas_rect_lists.append(self.canvas_rect)
                self.canvas_rect = None

    def mouseMoveEvent(self, mouse_event: QMouseEvent) -> None:
        pos = mouse_event.pos() 
        self.end = pos
        if self.is_masking:
            self.has_mask = True
            self.create_rect()
        elif self.is_moving:
            self.tools_form.setVisible(False)
            self.on_move()
        elif self.is_adjusting:
            self.on_adjust()
            self.tools_form.setVisible(False)
        elif self.is_drawing:
            self.on_tagging()
        
        # 设置鼠标样式
        if not self.is_drawing:
            if self.has_mask :
                if self.is_moving:
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.set_mouse_shape(pos)
            else:
                self.mouse_pos = ''
                self.setCursor(Qt.CrossCursor)

    def set_mouse_shape(self, pos: QPoint):
        """设置鼠标样式"""
        if self.rect_top_left.contains(pos):
            self.setCursor(Qt.SizeFDiagCursor)
            self.mouse_pos = 'TL'
        elif self.rect_bottom_left.contains(pos):
            self.setCursor(Qt.SizeBDiagCursor)
            self.mouse_pos = 'BL'
        elif self.rect_bottom_right.contains(pos):
            self.setCursor(Qt.SizeFDiagCursor)
            self.mouse_pos = 'BR'
        elif self.rect_top_right.contains(pos):
            self.setCursor(Qt.SizeBDiagCursor)
            self.mouse_pos = 'TR'
        elif self.rect_left.contains(pos):
            self.setCursor(Qt.SizeHorCursor)
            self.mouse_pos = 'L'
        elif self.rect_top.contains(pos):
            self.setCursor(Qt.SizeVerCursor)
            self.mouse_pos = 'T'
        elif self.rect_bottom.contains(pos):
            self.setCursor(Qt.SizeVerCursor)
            self.mouse_pos = 'B'
        elif self.rect_right.contains(pos):
            self.setCursor(Qt.SizeHorCursor)
            self.mouse_pos = 'R'
        elif self.mask_rect.contains(pos) and not self.is_tagging:
            self.setCursor(Qt.SizeAllCursor)
            self.mouse_pos = 'mask'
        elif self.mask_rect.contains(pos):
            self.setCursor(Qt.CrossCursor)  
            self.setMouseTracking(True)
            self.mouse_pos = 'tag'

    def update_mask_info(self):
        """更新蒙版信息"""
        # 蒙版点位
        self.mask_top_left = self.mask_rect.topLeft()
        self.mask_bottom_left = self.mask_rect.bottomLeft()
        self.mask_top_right =self.mask_rect.topRight()
        self.mask_bottom_right = self.mask_rect.bottomRight()
        self.mask_top_mid = (self.mask_top_left + self.mask_top_right) / 2
        self.mask_bottom_mid = (self.mask_bottom_left + self.mask_bottom_right) / 2
        self.mask_left_mid = (self.mask_top_left + self.mask_bottom_left) / 2
        self.mask_right_mid = (self.mask_top_right + self.mask_bottom_right) / 2

        # 框选区点位
        self.rect_top_left = QRectF(self.screen_top_left, self.mask_top_left)
        self.rect_bottom_left = QRectF(self.screen_bottom_left, self.mask_bottom_left)
        self.rect_top_right = QRectF(self.screen_top_right, self.mask_top_right)
        self.rect_bottom_right = QRectF(self.screen_bottom_right, self.mask_bottom_right)
        self.rect_top = QRectF(QPoint(self.mask_rect.left(), self.screen_top), self.mask_top_right)
        self.rect_bottom = QRectF(self.mask_bottom_left, QPoint(self.mask_rect.right(), self.screen_bottom))
        self.rect_left = QRectF(QPoint(self.screen_left, self.mask_rect.top()), self.mask_bottom_left)
        self.rect_right = QRectF(self.mask_top_right, QPoint(self.screen_right, self.mask_rect.bottom()))

    def paintEvent(self, paint_event: QPaintEvent) -> None:
        painter = QPainter()

        def draw_on_window(rect: typing.Union[QRectF, QRect], canvas):
            painter.begin(self)
            painter.drawPixmap(rect, canvas)
            painter.end()

        # 在画布层会话
        if self.is_drawing or self.is_tagging:
            painter.begin(self.canvas)
            self.paint_canvas(painter)
            painter.end()
            # 将画布层绘制到窗口上
            draw_on_window(
                self.screen_rect if isinstance(self.screen_rect, QRect) else self.get_rect(self.screen_rect), 
                self.canvas,
            )
            self.canvas = self.adjustment.copy()            
        # 在调节器上绘画
        else:
            self.adjustment = self.adjustment_original.copy()
            painter.begin(self.adjustment)
            self.paint_adjustment(painter)
            painter.end()  
            draw_on_window(
                self.get_rect(self.screen_rect),
                self.adjustment
            )      
            self.canvas = self.adjustment.copy()

    def paint_adjustment(self, painter: QPainter):
        if self.has_mask:
            painter.setRenderHint(QPainter.Antialiasing, True)  # 反走样
            painter.setPen(Qt.NoPen)
            # 在蒙版区绘制屏幕背景
            painter.setBrush(QBrush(self.screen))
            painter.drawRect(self.mask_rect)
            # 绘制线框
            lineWidth = self.adjustment_line_width
            painter.setBrush(self.blue)
            painter.drawRect(
                QRectF(
                    self.mask_top_left + QPoint(-lineWidth, -lineWidth),
                    self.mask_top_right + QPoint(lineWidth, 0))
            )
            painter.drawRect(
                QRectF(
                    self.mask_bottom_left + QPoint(-lineWidth, 0),
                    self.mask_bottom_right + QPoint(lineWidth, lineWidth)
                )
            )
            painter.drawRect(
                QRectF(
                    self.mask_top_left + QPoint(-lineWidth, -lineWidth),
                    self.mask_bottom_left + QPoint(0, lineWidth)
                )
            )
            painter.drawRect(
                QRectF(
                    self.mask_top_right + QPoint(0, -lineWidth),
                    self.mask_bottom_right + QPoint(lineWidth, lineWidth)
                )
            )
            if self.mask_rect.width() >= 150 and self.mask_rect.height() >= 150:
                # 绘制点
                points = [
                    self.mask_top_left, self.mask_top_right, self.mask_bottom_left, self.mask_bottom_right,
                    self.mask_left_mid, self.mask_right_mid, self.mask_top_mid, self.mask_bottom_mid
                ]
                # -白点
                whiteDotRadiusPoint = QPoint(self.adjustment_white_dot_radius, self.adjustment_white_dot_radius)
                painter.setBrush(Qt.white)
                for point in points:
                    painter.drawEllipse(QRectF(point - whiteDotRadiusPoint, point + whiteDotRadiusPoint))
                # -蓝点
                blueDotRadius = QPoint(self.adjustment_blue_dot_radius, self.adjustment_blue_dot_radius)
                painter.setBrush(self.blue)
                for point in points:
                    painter.drawEllipse(QRectF(point - blueDotRadius, point + blueDotRadius))

            # 绘制尺寸
            maskSize = (abs(int(self.mask_rect.width())), abs(int(self.mask_rect.height())))
            painter.setFont(QFont('Monaco', 7, QFont.Bold))
            painter.setPen(Qt.transparent)  # 透明获得字体Rect
            textRect = painter.drawText(
                QRectF(self.mask_top_left.x() + 10, self.mask_top_left.y() - 25, 100, 20),
                Qt.AlignLeft | Qt.AlignVCenter,
                '{} x {}'.format(*maskSize)
            )
            painter.setBrush(QColor(0, 0, 0, 128))  # 黑底
            padding = 5
            painter.drawRect(
                QRectF(
                    textRect.x() - padding,
                    textRect.y() - padding * 0.4,
                    textRect.width() + padding * 2,
                    textRect.height() + padding * 0.4
                )
            )
            painter.setPen(Qt.white)
            painter.drawText(
                textRect,
                Qt.AlignLeft | Qt.AlignVCenter,
                '{} x {}'.format(*maskSize)
            )
            painter.setPen(Qt.NoPen)

    def paint_canvas(self, painter: QPainter):
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(Qt.red,  1, Qt.SolidLine))
            if len(self.canvas_rect_lists) > 0:
                for rect in self.canvas_rect_lists:
                    painter.drawRect(rect)
            painter.drawRect(self.canvas_rect)
        except Exception as e:
            return   

    def keyPressEvent(self, key_event: QKeyEvent):
        if key_event.key() == Qt.Key_Escape:
            self.tools_form.close()
            self.close()
            return
        if key_event.key() == Qt.Key_Return or key_event.key() == Qt.Key_Enter:
            self.save()
            self.tools_form.close()
            self.close()
            return
        if key_event.modifiers() & Qt.ShiftModifier:
            self.is_shifting = True
    
    @typing.overload
    def save(self, pixmap: QPixmap):
        ...

    @typing.overload
    def save(slef):
        ...

    def save(self, pixmap: typing.Optional[QPixmap]=None):

        if pixmap is not None and isinstance(pixmap, QPixmap):
            return pixmap.save(
                'Screenshot.png',
                'PNG',
                100
            )
        self.output: QPixmap = self.screen.copy()
        # if self.has_pattern:
        #     painter = QPainter(self.output)
        #     painter.drawPixmap(self.canvas)
        self.output = self.output.copy(self.get_rect(self.mask_rect))
        if self.receivers(self.save_signal_data) > 0:
           self.save_signal_data.emit(self.output)
           return

        self.output.save(
            'test.png',
            'PNG',
            100
        )

    @staticmethod
    def get_rect_f(rect: QRect):
        return QRectF(
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height()
        )
    
    @staticmethod
    def get_rect(rectF: QRectF):
        return QRect(
            rectF.x(),
            rectF.y(),
            rectF.width(),
            rectF.height()
        )

    @staticmethod
    def normalize_rect(rect: QRectF):
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()
        if w < 0:
            x = x + w
            w = -w
        if h < 0:
            y = y + h
            h = -h
        return QRectF(x, y, w, h)
      
if __name__ == '__main__':
    app = QApplication.instance() or QApplication(sys.argv)
    win = ScreenWidget()
    try:
        win.show()
        app.exec_()
    except Exception as e:
        win.close()

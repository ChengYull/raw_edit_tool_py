from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QImage, QPalette, QTransform
from PyQt6.QtWidgets import (
    QWidget, QFileDialog, QMessageBox, QLineEdit, QPushButton,
    QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem,
    QSizePolicy, QDoubleSpinBox, QRadioButton, QComboBox, QApplication, QCheckBox, QProgressDialog, QTabWidget
)


class PaintWidget(QWidget):
    # 信号
    mouse_pressed = pyqtSignal()
    mouse_released = pyqtSignal()
    mouse_moved = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        # 图像数据相关
        self.m_q_img = QImage()
        self.m_is_img_load = False
        self.m_scaled_img_width = None
        self.m_scaled_img_height = None
        # 缩放倍数
        self.m_scale = 1.0
        self.zoom_in_ratio = 1.2
        self.zoom_out_ratio = 0.8
        self.min_scale = 0.05
        self.max_scale = 40.0
        # 逆矩阵
        self.inverse_transform = None # 用于坐标变换
        # 绘制相关
        self.m_mouse_point = QPoint()
        self.m_draw_point = QPoint(0, 0)  # 绘制起点

        # 鼠标相关
        self.setMouseTracking(True)  # 启用鼠标跟踪  即使鼠标没有点击也会触发move事件
        self.m_is_mouse_pressed = False
        self.m_enabel_move = True

        # 界面相关
        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.setStyleSheet("background-color: red;")
    def setImage(self, image):
        self.m_q_img = image
        self.m_is_img_load = True
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        if self.m_is_img_load:
            # 保存原始绘图状态
            painter.save()
            painter.translate(self.m_draw_point) # 移动到绘制起点
            painter.scale(self.m_scale, self.m_scale)
            self.m_scaled_img_width = self.m_q_img.width() * self.m_scale
            self.m_scaled_img_height = self.m_q_img.height() * self.m_scale
            # 从界面Widget坐标 映射到 图像像素坐标
            widget_rect = QRect(0, 0, self.width(), self.height())
            self.inverse_transform, res = painter.transform().inverted()  # 获取逆矩阵
            img_view_rect = self.inverse_transform.mapRect(widget_rect)
            # print(img_view_rect)
            # 绘制
            painter.drawImage(img_view_rect, self.m_q_img, img_view_rect)

        painter.restore() # 恢复状态

    def setZoom(self, scale):

        self.m_scale = self.bound(self.min_scale, self.max_scale, self.max_scale)
        self.update()

    def zoomIn(self):
        self.setZoom(self.m_scale * self.zoom_in_ratio)

    def zoomOut(self):
        self.setZoom(self.m_scale * self.zoom_out_ratio)

    def mouseMoveEvent(self, event):
        if self.m_is_img_load and self.m_is_mouse_pressed and self.m_enabel_move:
            delta = event.pos() - self.m_mouse_point
            self.m_draw_point += delta
            # 防止图片移出范围
            if self.m_draw_point.x() < 0 and self.m_scaled_img_width < self.width():
                self.m_draw_point = QPoint(0, self.m_draw_point.y())
            if self.m_draw_point.y() < 0 and self.m_scaled_img_height < self.height():
                self.m_draw_point = QPoint(self.m_draw_point.x(), 0)

            if (self.m_draw_point.x() + self.m_scaled_img_width  > self.width()
                    and self.m_scaled_img_width < self.width()):
                self.m_draw_point = QPoint(int(self.width() - self.m_scaled_img_width), self.m_draw_point.y())

            if (self.m_draw_point.y() + self.m_scaled_img_height > self.height()
                    and self.m_scaled_img_height < self.height()):
                self.m_draw_point = QPoint(self.m_draw_point.x(), int(self.height() - self.m_scaled_img_height))

            self.update()

        self.m_mouse_point = event.pos()
        self.mouse_moved.emit()

    def mousePressEvent(self, event):
        if self.m_is_img_load and event.button() == Qt.MouseButton.LeftButton:
            self.m_mouse_point = event.pos()
            self.m_is_mouse_pressed = True

        self.mouse_pressed.emit()

    def mouseReleaseEvent(self, event):
        if self.m_is_img_load and event.button() == Qt.MouseButton.LeftButton:
            self.m_is_mouse_pressed = False

        self.mouse_released.emit()

    def bound(self,min_val, val, max_val):
        return max(min_val, min(val, max_val))

    def wheelEvent(self, event):

        old_scale = self.m_scale
        flag = event.angleDelta().y()
        ratio = self.zoom_out_ratio
        if flag > 0:
            ratio = self.zoom_in_ratio

        self.m_scale = old_scale * ratio
        if self.m_scale < self.min_scale or self.m_scale > self.max_scale:
            self.m_scale = old_scale
            return
        # 以中心点缩放
        pos = event.position().toPoint()
        if self.rect().contains(pos):
            new_x = pos.x() - (pos.x() - self.m_draw_point.x()) * ratio
            new_y = pos.y() - (pos.y() - self.m_draw_point.y()) * ratio
            self.m_draw_point = QPoint(int(new_x), int(new_y))
        else:
            # 以图片中心缩放
            old_center = self.rect().center()
            new_width = self.width() * self.m_scale
            new_height = self.height() * self.m_scale
            self.m_draw_point = QPoint(int(old_center.x() - new_width / 2), int(old_center.y() - new_height / 2))

        self.update()


    def widgetToImagePos(self, widget_pos):
        """将界面坐标转换为图像像素坐标"""
        if not self.m_is_img_load:
            return None
        image_pos = self.inverse_transform.map(widget_pos)

        # 检查坐标是否在图像范围内
        if (0 <= image_pos.x() < self.m_q_img.width() and
                0 <= image_pos.y() < self.m_q_img.height()):
            return image_pos
        return None

    def getImgPos(self):
        return self.widgetToImagePos(self.m_mouse_point)

    def draw_img(self, img_pos, color, width=5):
        """在图像上绘制点"""
        if not self.m_is_img_load:
            return
        if img_pos is not None:
            painter = QPainter(self.m_q_img)
            pen = painter.pen()
            pen.setColor(color)
            pen.setWidth(width)
            painter.setPen(pen)
            painter.drawPoint(img_pos)
            painter.end()
            self.update()

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QImage, QDropEvent, QDragEnterEvent, QColor, QIcon, QCursor
from PyQt6.QtWidgets import (
    QWidget, QFileDialog, QMessageBox, QLineEdit, QPushButton,
    QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem,
    QSizePolicy, QDoubleSpinBox, QRadioButton, QComboBox, QApplication, QCheckBox, QProgressDialog, QTabWidget,
    QGroupBox
)
import time, os
from .paint_widget import PaintWidget
from .raw_process_util import raw_to_QImage, read_raw, qimage_to_raw_rgb, qimage_to_raw_gray, raw8_to_unpack16bit
class MainWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True) # 启用拖放功能
        self.setWindowTitle('Raw图编辑')
        self.paintWidget = PaintWidget()
        self.imgWidthLineEdit = QLineEdit()
        self.imgHeightLineEdit = QLineEdit()
        self.loadImgBtn = QPushButton("加载图片")
        self.drawImgBtn = QPushButton("绘制")
        self.colorRLineEdit = QLineEdit()
        self.colorGLineEdit = QLineEdit()
        self.colorBLineEdit = QLineEdit()
        self.saveBtn = QPushButton("保存")
        self.setUI()
        self.setup_connections()
        self.img_copy = None
        self.raw_info = None
        # self.img = QImage("D:\\Pictures\\theme.png")

        # self.paintWidget.setImage(self.img)

        # 图像显示状态
        self.show_mode = "RGB"  # "GRAY" 或 "RGB"

        # 绘制状态
        self.is_drawing = False
        self.is_raw_img = False
        self.raw_test()


    def raw_test(self):
        raw_path = r"E:\project\RPSFR\img\__Idx1__Raw_20250402T172520.4064X3048.unpack10_grbg.vcmpos_843.raw"
        raw_info = read_raw(raw_path)
        if not raw_info:
            return
        raw_qimage = raw_to_QImage(raw_info['raw_data'], raw_info['raw_width'], raw_info['raw_height'], raw_info['pattern'], "RGB")
        self.paintWidget.setImage(raw_qimage)


    def setUI(self):
        self.resize(800, 600)
        # 主布局
        mainLayout = QVBoxLayout()

        # 画布布局
        mainHLayout = QHBoxLayout()
        mainHLayout.addWidget(self.paintWidget)

        # 操作栏
        opLayout = QVBoxLayout()

        imgGroupBox = QGroupBox("图片信息")
        imgGroupBox.setMaximumWidth(150)
        imgGroupBox.setMaximumHeight(250)
        groupBoxLayout = QVBoxLayout()


        imgWidthLabel = QLabel("宽：")
        imgHeightLabel = QLabel("高：")

        # 宽高显示
        widthLayout = QHBoxLayout()
        widthLayout.addWidget(imgWidthLabel)
        widthLayout.addWidget(self.imgWidthLineEdit)
        heightLayout = QHBoxLayout()
        heightLayout.addWidget(imgHeightLabel)
        heightLayout.addWidget(self.imgHeightLineEdit)

        groupBoxLayout.addWidget(self.loadImgBtn)
        groupBoxLayout.addLayout(widthLayout)
        groupBoxLayout.addLayout(heightLayout)
        imgGroupBox.setLayout(groupBoxLayout)

        drawGroupBox = QGroupBox("绘制")
        drawGroupBox.setMaximumWidth(150)
        drawGroupBox.setMaximumHeight(150)
        drawGroupBoxLayout = QVBoxLayout()

        # 添加内容
        colorEditLayout = QHBoxLayout()
        colorEditLayout.addWidget(QLabel("R:"))
        colorEditLayout.addWidget(self.colorRLineEdit)
        colorEditLayout.addWidget(QLabel("G:"))
        colorEditLayout.addWidget(self.colorGLineEdit)
        colorEditLayout.addWidget(QLabel("B:"))
        colorEditLayout.addWidget(self.colorBLineEdit)

        drawGroupBoxLayout.addLayout(colorEditLayout)
        drawGroupBoxLayout.addWidget(self.drawImgBtn)
        """..."""
        drawGroupBox.setLayout(drawGroupBoxLayout)

        otherGroupBox = QGroupBox("其他")
        otherGroupBox.setMaximumWidth(150)
        otherGroupBox.setMaximumHeight(150)
        otherGroupBoxLayout = QVBoxLayout()
        # 添加内容
        otherGroupBoxLayout.addWidget(self.saveBtn)

        otherGroupBox.setLayout(otherGroupBoxLayout)

        opLayout.addWidget(imgGroupBox)
        opLayout.addWidget(drawGroupBox)
        opLayout.addWidget(otherGroupBox)

        mainHLayout.addLayout(opLayout)
        mainLayout.addLayout(mainHLayout)

        self.setLayout(mainLayout)

    # 连接信号与槽
    def setup_connections(self):
        self.loadImgBtn.clicked.connect(self.on_load_img_clicked)
        self.drawImgBtn.clicked.connect(self.on_draw_btn_clicked)
        self.paintWidget.mouse_moved.connect(self.draw_event)
        self.saveBtn.clicked.connect(self.on_save_btn_clicked)


    def on_load_img_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.raw;*.bmp;*.jpg;*.png)")
        if not file_path:
            return
        self.show_img(file_path)




    def show_img(self, file_path):
        file_name = os.path.basename(file_path)
        surfix = os.path.splitext(file_name)[1].lower()
        if surfix == ".bmp" or surfix == ".jpg" or surfix == ".png":
            img = QImage(file_path)
            if img.isNull():
                QMessageBox.critical(self, "错误", "无法加载图片")
                return
            self.is_raw_img = False
            self.img_copy = img
            self.paintWidget.setImage(img)
            self.imgWidthLineEdit.setText(str(img.width()))
            self.imgHeightLineEdit.setText(str(img.height()))
            return
        elif surfix == ".raw":
            img_info = read_raw(file_path)
            if not img_info:
                QMessageBox.critical(self, "错误", "无法加载图片, 不支持的raw图类型")
                return
            img = raw_to_QImage(img_info['raw_data'], img_info['raw_width'], img_info['raw_height'], img_info['pattern'],
                            self.show_mode)
            self.is_raw_img = True
            self.img_copy = img
            self.raw_info = img_info
            self.paintWidget.setImage(img)
            self.imgWidthLineEdit.setText(str(img_info['raw_width']))
            self.imgHeightLineEdit.setText(str(img_info['raw_height']))
        else:
            QMessageBox.critical(self, "错误", "不支持的文件类型")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入时检查文件类型"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """释放文件时触发，只支持单个文件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            print(urls)
            # 检查文件数量
            if len(urls) != 1:
                QMessageBox.critical(self, "错误", "只支持拖入单个文件，请重新拖拽")
                event.ignore()
                return

            # 检查是否为文件夹
            file_path = urls[0].toLocalFile()
            if os.path.isdir(file_path):
                QMessageBox.critical(self, "错误", "不支持拖入文件夹，请拖入单个文件")
                event.ignore()
                return

            event.acceptProposedAction()

            # 显示图片
            self.show_img(file_path)

        else:
            event.ignore()


    def on_draw_btn_clicked(self):
        """绘制按钮点击事件"""
        if self.paintWidget.m_q_img is None:
            QMessageBox.warning(self, "提示", "请先加载图片")
            return
        if not self.is_drawing:
            self.is_drawing = True
            self.paintWidget.m_enabel_move = False

            current_dir = os.path.dirname(os.path.abspath(__file__))
            svg_path = os.path.join(current_dir, "../resource/pen.svg")
            pen_icon = QIcon(svg_path)
            pixmap = pen_icon.pixmap(QSize(32, 32))
            pen_cursor = QCursor(pixmap, hotX=2, hotY=28)
            self.setCursor(pen_cursor)

            # 设置按钮文本
            self.drawImgBtn.setText("结束绘制")

        else:
            self.is_drawing = False
            self.paintWidget.m_enabel_move = True
            # 恢复默认鼠标光标
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.drawImgBtn.setText("绘制")

    def get_color_from_input(self):
        """从输入框获取颜色值，默认为黑色"""
        try:
            r = int(self.colorRLineEdit.text()) if self.colorRLineEdit.text() else 0
            g = int(self.colorGLineEdit.text()) if self.colorGLineEdit.text() else 0
            b = int(self.colorBLineEdit.text()) if self.colorBLineEdit.text() else 0
            return QColor(r, g, b)
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的颜色值（0-255）")
            return QColor(0, 0, 0)

    def draw_event(self):
        """绘制事件处理"""
        if not self.is_drawing:
            return

        if self.paintWidget.m_is_mouse_pressed:
            color = self.get_color_from_input()
            img_pos = self.paintWidget.getImgPos()
            self.paintWidget.draw_img(img_pos, color, 5)


    def on_save_btn_clicked(self):
        """保存图片"""
        if self.paintWidget.m_q_img is None:
            QMessageBox.warning(self, "提示", "没有图片可保存")
            return

        default_name = ""
        if self.is_raw_img:
            img_types = "RAW Images (*.raw);;"
            default_name = self.raw_info["origin_name"]
        else:
            img_types = "PNG Images (*.png);;JPEG Images (*.jpg);;BMP Images (*.bmp)"
        file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_name, img_types)
        if not file_path:
            return

        if self.is_raw_img:
            origin_type = self.raw_info["origin_type"]
            pattern = self.raw_info["pattern"]
            if self.show_mode == "RGB":  # 拿到raw8数据
                raw_data = qimage_to_raw_rgb(self.paintWidget.m_q_img, pattern)
            else:
                raw_data = qimage_to_raw_gray(self.paintWidget.m_q_img)
            if origin_type != "raw8":
                raw_data = raw8_to_unpack16bit(raw_data, origin_type)

            # 直接保存为raw文件
            try:
                with open(file_path, "wb") as f:
                    f.write(raw_data)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存图片失败: {str(e)}")
        # 非raw图直接使用QImage的保存功能
        else :
            if not self.paintWidget.m_q_img.save(file_path):
                QMessageBox.critical(self, "错误", "保存图片失败")

        QMessageBox.information(self, "成功", f"图片保存成功到{file_path}")
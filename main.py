import os
import re
import sys
import shutil
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QMainWindow
from PyQt5.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QPushButton, QLabel
 
 
class StartupDialog(QDialog):  # 参数获取
    def __init__(self, parent=None):
        super(StartupDialog, self).__init__(parent)
 
        self.setWindowTitle("参数设置")  # 对话框标题
        self.resize(500, 200)  # 对话框尺寸
        
        self.img_path_label = QLabel("待分类图像路径")
        self.img_path_line_edit = QLineEdit("C:/Users/DELL/Desktop/before/")
        self.output_path_label = QLabel("分类后保存路径")
        self.output_path_line_edit = QLineEdit("C:/Users/DELL/Desktop/result/")
        self.category_label = QLabel("类别名称（以空格分隔）")
        self.category_line_edit = QLineEdit("red black other")
        self.idx = QLabel("当前标注进度（从第几张开始）")
        self.idx_edit = QLineEdit("0")
 
        layout = QVBoxLayout()
        layout.addWidget(self.img_path_label)
        layout.addWidget(self.img_path_line_edit)
        layout.addWidget(self.output_path_label)
        layout.addWidget(self.output_path_line_edit)
        layout.addWidget(self.category_label)
        layout.addWidget(self.category_line_edit)
        layout.addWidget(self.idx)
        layout.addWidget(self.idx_edit)
 
        button = QPushButton("确定")
        button.clicked.connect(self.accept)  # 当单击"确定"按钮时，关闭对话框
        layout.addWidget(button)
 
        self.setLayout(layout)
 
    def getValues(self):
        img_path = self.img_path_line_edit.text()
        output_path = self.output_path_line_edit.text()
        categories = self.category_line_edit.text().split(' ')
        idx = self.idx_edit.text()
        return img_path, output_path, categories, idx
 
 
class Classification_Window(QMainWindow):  # 进行分类
 
    MAIN_IMAGE_SIZE = 640       # 主图像的尺寸
    OTHER_IMAGE_SIZE = 120      # 其他图像的尺寸
    BUTTON_HEIGHT = 35          # 按钮的高度
    BUTTON_WIDTH = 110          # 按钮宽度
    BUTTON_SPACING = 20         # 按钮间距
    BOTTOM_MARGIN = 10          # 底部的边距
    X_COORDINATE_INIT = 100     # x坐标的初始值
    BUTTON_BOTTOM_MARGIN = 20   # 按钮相对于窗口底部的位置
    WINDOW_WIDTH = 1200         # 窗口的宽度
    WINDOW_HEIGHT = 800         # 窗口的高度
    FONT_PIXEL_SIZE = 18        # 字体的像素尺寸
 
    def __init__(self, img_path, output_path, button_list, idx=0):
        super(Classification_Window, self).__init__()
        self.img_path = img_path            # 图像的路径
        self.output_path = output_path      # 输出的路径     
        self.img_list = os.listdir(self.img_path)  # 获取图像路径下的所有文件名
        self.idx = idx                      # 当前图像的索引
        self.buttons = []                   # 按钮列表
        self.lbl_list = []                  # 标签列表
        self.is_first = True if idx == 0 else False   # 是否是第一次打开
        self.initUI(button_list)            # 初始化用户界面
        self.show()                         # 显示窗口
        self.zoom_factor = 1.0              # 初始缩放因子为1
 
    # 初始化用户界面
    def initUI(self, button_list):
        self.initWindow() 
        self.initButtons(button_list)
        self.initLabels()
 
    # 初始化窗口
    def initWindow(self):
        font = QFont()
        font.setPixelSize(self.FONT_PIXEL_SIZE)
        self.setWindowTitle("label_me") 
        self.resize(QSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
 
    # 初始化按钮
    def initButtons(self, button_list):
        self.button_list = button_list  
        self.category_to_number = {name: str(idx + 1) for idx, name in enumerate(self.button_list)}
            
        font = QFont()
        font.setPixelSize(self.FONT_PIXEL_SIZE)
        # 添加上一张和下一张图像的按钮
        self.prev_button = QPushButton("Prev(←)", self)
        self.prev_button.setFont(font)
        self.prev_button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)  # 设置固定大小
        self.prev_button.move(0, self.height() - self.BUTTON_HEIGHT - self.BUTTON_BOTTOM_MARGIN)
        self.prev_button.clicked.connect(self.prev_image)
        self.prev_button.setFocusPolicy(Qt.NoFocus)  # 禁用按钮焦点
 
        self.next_button = QPushButton("Next(→)", self)
        self.next_button.setFont(font)
        self.next_button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)  # 设置固定大小
        self.next_button.move(self.BUTTON_WIDTH + self.BUTTON_SPACING, self.height() - self.BUTTON_HEIGHT - self.BUTTON_BOTTOM_MARGIN)  # 修改，设置位置
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setFocusPolicy(Qt.NoFocus)  # 禁用按钮焦点
 
        self.key_to_button = {Qt.Key_Left: self.prev_button, Qt.Key_Right: self.next_button}  # 更新映射
 
        for idx, label_name in enumerate(self.button_list):
            button = QPushButton(f"{label_name}({self.category_to_number[label_name]})", self)  # 创建按钮
            button.setFont(font)
            button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)  # 设置固定大小
            button_y = self.height() - self.BUTTON_HEIGHT - self.BUTTON_BOTTOM_MARGIN
            # 设置位置，将每个按钮的位置根据其索引值、按钮宽度和按钮间距进行设置
            button.move((idx + 2) * (self.BUTTON_WIDTH + self.BUTTON_SPACING), button_y)
            button.clicked.connect(self.classify)  
            button.setFocusPolicy(Qt.NoFocus)  # 禁用按钮焦点
            self.buttons.append(button)  
 
    # 初始化标签
    def initLabels(self):
        max_image_y = self.height() - self.BUTTON_HEIGHT - self.BOTTOM_MARGIN - self.BUTTON_BOTTOM_MARGIN 
        x_coordinate = self.X_COORDINATE_INIT 
 
        for i in range(self.get_remainder()):
            self.pix = QPixmap(self.img_path + self.img_list[self.idx + i])
            label_img = QLabel(self)
            
            if self.is_first and i == 0 or not self.is_first and i == 1:
                display_size = self.MAIN_IMAGE_SIZE
            else:
                display_size = self.OTHER_IMAGE_SIZE
 
            label_img.setGeometry(x_coordinate, max_image_y - display_size, display_size, display_size)
            x_coordinate += display_size
 
            max_dim = max(self.pix.width(), self.pix.height())
            scale_factor = display_size / max_dim
            scaled_pix = self.pix.scaled(int(self.pix.width() * scale_factor), int(self.pix.height() * scale_factor), Qt.KeepAspectRatio)
 
            label_img.setPixmap(scaled_pix)
            label_img.setScaledContents(False)
 
            self.lbl_list.append(label_img)
 
    # 获取剩余的图像数量
    def get_remainder(self):
        r = len(self.img_list) - self.idx
        if r > 4:
            r = 4
        if self.is_first:
            r = min(3, r)
        return r
 
    # 显示前一张图片
    def prev_image(self):
        if self.idx > 0:
            self.idx -= 1
            if self.idx == 0:
                self.is_first = True
            self.update_image()
 
    # 显示下一张图片
    def next_image(self):
        if self.idx < len(self.img_list) - 1:
            self.idx += 1
            self.update_image()

    # 鼠标滚轮事件处理方法
    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            # 每次滚轮事件调整10%的缩放
            delta = event.angleDelta().y() / 120  # 获取滚动步长，通常一步是120
            if delta > 0:
                self.zoom_factor *= 1.1
            elif delta < 0:
                self.zoom_factor *= 0.9
            self.update_image()  # 更新图像显示以反映新的缩放比例
            event.accept()
        else:
            event.ignore()

    # 更新图片
    def update_image(self):
        start = max(self.idx - 1, 0)
        end = start + 4 if self.idx > 0 else start + 3
        img_full_path = [self.img_path + self.img_list[i] for i in range(start, min(end, len(self.img_list)))]
 
        while len(self.lbl_list) < len(img_full_path): 
            self.lbl_list.append(QLabel(self))
 
        self.clear_lbls()
        x_coordinate = self.X_COORDINATE_INIT
 
        for i in range(len(img_full_path)):
            pix = QPixmap(img_full_path[i])
            if i == self.idx - start:
                display_size = self.MAIN_IMAGE_SIZE * self.zoom_factor  # 应用缩放因子
            else:
                display_size = self.OTHER_IMAGE_SIZE * self.zoom_factor  # 应用缩放因子
 
            max_dim = max(pix.width(), pix.height())
            scale_factor = display_size / max_dim
            scaled_pix = pix.scaled(int(pix.width() * scale_factor), int(pix.height() * scale_factor), Qt.KeepAspectRatio)
            label_img = self.lbl_list[i]
            label_img.setPixmap(scaled_pix)
 
            max_image_y = self.height() - self.BUTTON_HEIGHT - self.BOTTOM_MARGIN - self.BUTTON_BOTTOM_MARGIN 
            label_img.setGeometry(x_coordinate, max_image_y - display_size, display_size, display_size)
            x_coordinate += display_size
 
            label_img.show()
        self.setWindowTitle("当前是第 %d 个图片" % self.idx)
 
    # 清空所有标签
    def clear_lbls(self):
        for i in range(len(self.lbl_list)):
            self.lbl_list[i].hide()
 
    # 复制图像
    def copyfile(self, srcfile, dstfile):
        if not os.path.isfile(srcfile):
            print("%s does not exist!" % srcfile)
        else:
            f_path, f_name = os.path.split(dstfile)
            if not os.path.exists(f_path):
                os.makedirs(f_path)
            shutil.copyfile(srcfile, dstfile)
            print("Copied %s -> %s" % (srcfile, dstfile))
 
    # 删除旧图像
    def delete_old_image(self, current_img_path):
        for btn in self.button_list:
            old_dir_path = self.output_path + btn + "/"
            old_img_path = old_dir_path + current_img_path
            if os.path.isfile(old_img_path):
                os.remove(old_img_path)
                print(f"Deleted {old_img_path}")
 
    # 分类
    def classify(self, category=None):
        self.is_first = False
        if len(self.lbl_list) < 4: 
            for _ in range(4 - len(self.lbl_list)):
                self.lbl_list.append(QLabel(self))
 
        if not category:
            sender = self.sender()
            button_text = sender.text()
            category = re.match(r'([a-zA-Z]+)', button_text).group(1)  # 只获取文本中的字母
 
        dir_path = self.output_path + category + "/"
        current_img_path = self.img_list[self.idx]
 
        # 删除旧图像
        self.delete_old_image(current_img_path)
 
        # 复制文件到指定目录
        self.copyfile(self.img_path + current_img_path, dir_path + current_img_path)
        
        # 如果当前图像不是最后一张，显示下一张
        if self.idx < len(self.img_list) - 1:
            self.next_image()
 
        # 更新图片和标题
        self.update_image()
        self.setWindowTitle("当前是第 %d 个图片" % self.idx)
 
    # 按键事件处理
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:              # 左箭头按键：显示前一张图
            self.prev_image()
        elif key == Qt.Key_Right:           # 右箭头按键：显示下一张图
            self.next_image()
        elif Qt.Key_0 <= key <= Qt.Key_9:   # 数字键：分类
            number = str(key - Qt.Key_0)
            try:
                for category, category_number in self.category_to_number.items():
                    if category_number == number:
                        self.classify(category)
                        break
            except Exception as e:
                print(e)
 
 
if __name__ == '__main__':
    app = QApplication(sys.argv)  # 创建应用
    
    dialog = StartupDialog()
    if dialog.exec():
        img_path, output_path, button_list, idx = dialog.getValues()
        f = Classification_Window(img_path, output_path, button_list, int(idx))
 
    sys.exit(app.exec())  # 开始应用的事件循环

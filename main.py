import sys
import shutil
import logging
from pathlib import Path
from functools import partial
from typing import List, Dict, Optional

from PyQt5.QtCore import Qt, QSize, QSettings, QTimer
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QPushButton, QLabel, QMainWindow, QDialog, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QWidget, QShortcut,
    QInputDialog, QCheckBox, QSpacerItem, QSizePolicy, QListWidget, QListWidgetItem
)


class StartupDialog(QDialog):
    """
    启动对话框类。
    在程序开始时运行，用于收集用户配置，如路径、类别等。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("参数设置")
        self.setMinimumWidth(500)
        self.settings = QSettings("MyCorp", "ImageClassifier")

        self.img_path_label = QLabel("待分类图像路径:")
        self.img_path_line_edit = QLineEdit(self.settings.value("imgPath", "", str))
        self.img_path_button = QPushButton("浏览...")

        self.output_path_label = QLabel("分类后保存路径:")
        self.output_path_line_edit = QLineEdit(self.settings.value("outputPath", "", str))
        self.output_path_button = QPushButton("浏览...")

        self.category_label = QLabel("类别名称 (以空格分隔):")
        self.category_line_edit = QLineEdit(self.settings.value("categories", "red black other", str))

        self.log_label = QLabel("日志选项:")
        self.log_to_file_checkbox = QCheckBox("记录日志到文件 (在输出路径下创建 labeler.log)")
        self.log_to_console_checkbox = QCheckBox("在控制台打印日志")
        self.log_to_file_checkbox.setChecked(self.settings.value("logToFile", True, bool))
        self.log_to_console_checkbox.setChecked(self.settings.value("logToConsole", True, bool))

        self.ok_button = QPushButton("确定")

        layout = QVBoxLayout(self)
        img_path_layout = QHBoxLayout()
        img_path_layout.addWidget(self.img_path_line_edit)
        img_path_layout.addWidget(self.img_path_button)
        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(self.output_path_line_edit)
        output_path_layout.addWidget(self.output_path_button)

        layout.addWidget(self.img_path_label)
        layout.addLayout(img_path_layout)
        layout.addWidget(self.output_path_label)
        layout.addLayout(output_path_layout)
        layout.addWidget(self.category_label)
        layout.addWidget(self.category_line_edit)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_to_file_checkbox)
        layout.addWidget(self.log_to_console_checkbox)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.ok_button)

        self.img_path_button.clicked.connect(self.browse_img_path)
        self.output_path_button.clicked.connect(self.browse_output_path)
        self.ok_button.clicked.connect(self.on_accept)

    def browse_img_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择图片文件夹", self.img_path_line_edit.text())
        if path:
            self.img_path_line_edit.setText(path)

    def browse_output_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹", self.output_path_line_edit.text())
        if path:
            self.output_path_line_edit.setText(path)

    def on_accept(self) -> None:
        img_path = Path(self.img_path_line_edit.text())
        if not img_path.exists() or not img_path.is_dir():
            QMessageBox.warning(self, "路径错误", "待分类图像路径不存在或不是一个文件夹！")
            return
        if not self.category_line_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "类别名称不能为空！")
            return

        self.accept()

    def get_values(self) -> (Path, Path, List[str], bool, bool):
        """获取用户输入的所有值，并保存配置。不再返回起始索引。"""
        img_path = Path(self.img_path_line_edit.text())
        output_path = Path(self.output_path_line_edit.text())
        categories = self.category_line_edit.text().strip().split(' ')
        log_to_file = self.log_to_file_checkbox.isChecked()
        log_to_console = self.log_to_console_checkbox.isChecked()

        self.settings.setValue("imgPath", str(img_path))
        self.settings.setValue("outputPath", str(output_path))
        self.settings.setValue("categories", ' '.join(categories))
        self.settings.setValue("logToFile", log_to_file)
        self.settings.setValue("logToConsole", log_to_console)
        return img_path, output_path, categories, log_to_file, log_to_console


class ClassificationWindow(QMainWindow):
    MAIN_IMAGE_TARGET_SIZE: int = 640
    OTHER_IMAGE_TARGET_SIZE: int = 160

    def __init__(self, img_path: Path, output_path: Path, categories: List[str], log_to_file: bool,
                 log_to_console: bool):
        super().__init__()
        self.img_path = img_path
        self.output_path = output_path
        self.categories = categories
        self.img_list: List[Path] = sorted(
            [p for p in self.img_path.glob('*') if p.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])

        self.setup_logging(log_to_file, log_to_console)

        if not self.img_list:
            msg = "图片文件夹中没有找到任何支持的图片文件！"
            logging.critical(msg)
            QMessageBox.critical(self, "错误", msg)
            QTimer.singleShot(0, self.close)
            return

        self.total_images = len(self.img_list)
        self.idx = 0  # 默认从第一张开始
        self.last_action = None
        self.zoom_factor = 1.0
        self.current_pixmap: Optional[QPixmap] = None

        # --- 存储分类状态 ---
        self.classification_status: Dict[Path, str] = {}
        self.preload_existing_classifications()

        self.init_ui()
        QTimer.singleShot(0, self.update_view)
        self.show()
        logging.info("标注窗口初始化完成。")

    def setup_logging(self, log_to_file: bool, log_to_console: bool):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        if log_to_file:
            self.output_path.mkdir(parents=True, exist_ok=True)
            log_file = self.output_path / 'labeler.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        logging.info("日志系统已配置。")

    # --- 预加载已有分类 ---
    def preload_existing_classifications(self):
        """扫描输出目录，加载已有的分类信息。"""
        logging.info("开始扫描已有分类...")
        if not self.output_path.exists():
            return

        # 创建一个从文件名到完整路径的映射，以提高查找效率
        filename_to_path = {p.name: p for p in self.img_list}

        for cat_dir in self.output_path.iterdir():
            if cat_dir.is_dir() and cat_dir.name in self.categories:
                for img_file in cat_dir.glob('*'):
                    if img_file.name in filename_to_path:
                        original_path = filename_to_path[img_file.name]
                        self.classification_status[original_path] = cat_dir.name
        logging.info(f"扫描完成，加载了 {len(self.classification_status)} 条分类记录。")

    def init_ui(self) -> None:
        """初始化UI，创建所有窗口控件并设置布局。"""
        self.setWindowTitle("图像分类标注工具")
        self.resize(1600, 900)

        # --- 创建图片文件列表 ---
        self.image_list_widget = QListWidget()
        for img_path in self.img_list:
            self.image_list_widget.addItem(QListWidgetItem(img_path.name))
        self.image_list_widget.setFixedWidth(250)  # 给列表一个固定宽度

        # --- 图片显示区 ---
        image_display_layout = QHBoxLayout()
        self.image_labels: List[QLabel] = []
        for _ in range(4):
            label = QLabel(alignment=Qt.AlignCenter)
            self.image_labels.append(label)
            image_display_layout.addWidget(label)
        image_display_layout.setStretch(0, 1)
        image_display_layout.setStretch(1, 4)
        image_display_layout.setStretch(2, 1)
        image_display_layout.setStretch(3, 1)

        # --- 按钮区 ---
        # 将局部变量提升为实例属性
        self.button_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张 (←)")
        self.next_button = QPushButton("下一张 (→)")
        self.undo_button = QPushButton("撤销 (Ctrl+Z)")
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.undo_button)
        self.button_layout.addStretch()

        self.category_to_number: Dict[str, int] = {name: i + 1 for i, name in enumerate(self.categories)}
        for name in self.categories:
            self.create_category_button(name)

        self.add_category_button = QPushButton("新增类别")
        self.add_category_button.setToolTip("点击后可输入名称，动态添加一个新的分类按钮")
        self.button_layout.addWidget(self.add_category_button)

        # --- 右侧主布局 (图片 + 按钮 + 进度) ---
        right_v_layout = QVBoxLayout()
        self.progress_label = QLabel()
        right_v_layout.addLayout(image_display_layout, stretch=1)
        right_v_layout.addLayout(self.button_layout)
        right_v_layout.addWidget(self.progress_label)

        # --- 顶级主布局 (文件列表 + 右侧) ---
        main_h_layout = QHBoxLayout()
        main_h_layout.addWidget(self.image_list_widget)
        main_h_layout.addLayout(right_v_layout, stretch=1)

        central_widget = QWidget()
        central_widget.setLayout(main_h_layout)
        self.setCentralWidget(central_widget)

        # --- 信号与槽 & 快捷键 ---
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        self.undo_button.clicked.connect(self.undo_action)
        self.add_category_button.clicked.connect(self.add_new_category)
        # --- 连接列表点击事件 ---
        self.image_list_widget.currentItemChanged.connect(self.jump_to_image)

        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_image)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_image)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_action)

    # --- 列表跳转槽函数 ---
    def jump_to_image(self, current: QListWidgetItem, previous: QListWidgetItem):
        """当用户点击文件列表时，跳转到对应图片。"""
        if current is not None:
            row = self.image_list_widget.row(current)
            if self.idx != row:
                self.idx = row
                self.zoom_factor = 1.0  # 重置缩放
                self.update_view()

    def create_category_button(self, name: str):
        if name in self.category_to_number:
            num = self.category_to_number[name]
            button = QPushButton(f"{name} ({num})")
            button.clicked.connect(partial(self.classify, category=name))
            # 插入到“新增类别”按钮和伸缩项之前
            self.button_layout.insertWidget(self.button_layout.count() - 2, button)
            if num < 10:
                QShortcut(QKeySequence(str(num)), self, partial(self.classify, category=name))

    def add_new_category(self):
        text, ok = QInputDialog.getText(self, '添加新分类', '请输入新的类别名称:')
        if ok and text:
            new_category = text.strip()
            if not new_category:
                QMessageBox.warning(self, "输入无效", "类别名称不能为空。")
                return
            if new_category in self.categories:
                QMessageBox.information(self, "已存在", f"类别 '{new_category}' 已存在。")
                return
            self.categories.append(new_category)
            new_num = len(self.category_to_number) + 1
            self.category_to_number[new_category] = new_num
            self.create_category_button(new_category)
            logging.info(f"动态添加新分类: '{new_category}'")

    def update_view(self) -> None:
        indices_to_show = [self.idx - 1, self.idx, self.idx + 1, self.idx + 2]
        for i, label in enumerate(self.image_labels):
            img_idx = indices_to_show[i]
            is_main_image = (i == 1)
            if 0 <= img_idx < self.total_images:
                target_size = int(
                    self.MAIN_IMAGE_TARGET_SIZE * self.zoom_factor) if is_main_image else self.OTHER_IMAGE_TARGET_SIZE
                label.setStyleSheet("border: 3px solid #0078D7;" if is_main_image else "border: 1px solid #CCCCCC;")

                img_path = self.img_list[img_idx]
                pixmap = QPixmap(str(img_path))
                if is_main_image: self.current_pixmap = pixmap
                scaled_pixmap = pixmap.scaled(QSize(target_size, target_size), Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
                label.show()
            else:
                label.clear()
                label.setStyleSheet("border: none;")
                label.hide()

        current_img = self.img_list[self.idx]
        img_name = current_img.name
        img_dims = f"{self.current_pixmap.width()}x{self.current_pixmap.height()}px" if self.current_pixmap else "N/A"

        # --- 更新状态栏信息以显示分类 ---
        status = self.classification_status.get(current_img, "未分类")
        self.setWindowTitle(f"图像分类 - {img_name}")
        self.progress_label.setText(
            f"进度: {self.idx + 1} / {self.total_images} | {img_name} | {img_dims} | 分类状态: {status}")
        self.undo_button.setEnabled(self.last_action is not None)

        # --- 同步文件列表的选中项 ---
        self.image_list_widget.blockSignals(True)  # 临时阻塞信号，防止触发jump_to_image
        self.image_list_widget.setCurrentRow(self.idx)
        self.image_list_widget.blockSignals(False)  # 解除阻塞

    def classify(self, category: str) -> None:
        current_img_path = self.img_list[self.idx]
        target_dir = self.output_path / category

        # 查找此文件是否之前已被分类过
        old_path = self.find_file_in_categories(current_img_path.name)

        self.last_action = {
            "source": current_img_path,
            "target": target_dir / current_img_path.name,
            # --- 优化点: 记录旧的分类状态 ---
            "previous_status": self.classification_status.get(current_img_path)
        }

        # 如果之前分类过，先删除旧的分类文件
        if old_path:
            old_path.unlink()

        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current_img_path, target_dir)

        # --- 更新分类状态字典 ---
        self.classification_status[current_img_path] = category
        logging.info(f"分类: {current_img_path.name} -> {category}")

        if self.idx < self.total_images - 1:
            self.idx += 1
            self.zoom_factor = 1.0
        self.update_view()

    def find_file_in_categories(self, filename: str) -> Optional[Path]:
        if not self.output_path.exists(): return None
        for cat_dir in self.output_path.iterdir():
            if cat_dir.is_dir():
                target_file = cat_dir / filename
                if target_file.exists():
                    return target_file
        return None

    def undo_action(self) -> None:
        if not self.last_action: return
        action = self.last_action
        target_file = action["target"]
        source_img_path = action["source"]

        if target_file.exists():
            target_file.unlink()

        # --- 根据 previous_status 恢复状态字典 ---
        if action["previous_status"]:
            self.classification_status[source_img_path] = action["previous_status"]
            # 恢复旧文件 (注意：这会再次执行一次复制操作)
            old_target_path = self.output_path / action["previous_status"] / source_img_path.name
            old_target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_img_path, old_target_path)
        else:
            # 如果之前未分类，则从字典中删除
            if source_img_path in self.classification_status:
                del self.classification_status[source_img_path]

        self.idx = self.img_list.index(source_img_path)
        self.last_action = None
        self.update_view()
        logging.info(f"操作已撤销: 恢复 {action['source'].name}")

    def prev_image(self) -> None:
        if self.idx > 0:
            self.idx -= 1
            self.zoom_factor = 1.0
            self.update_view()

    def next_image(self) -> None:
        if self.idx < self.total_images - 1:
            self.idx += 1
            self.zoom_factor = 1.0
            self.update_view()

    def wheelEvent(self, event) -> None:
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            self.zoom_factor *= 1.15 if delta > 0 else (1 / 1.15)
            self.update_view()
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = StartupDialog()
    if dialog.exec():
        img_p, out_p, cats, log_f, log_c = dialog.get_values()
        main_window = ClassificationWindow(img_p, out_p, cats, log_f, log_c)
        if main_window.isVisible():
            sys.exit(app.exec())

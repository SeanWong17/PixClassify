# 🚀 PixClassify - 高效图像分类标注工具

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-PyQt5-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**PixClassify** 是一个使用 PyQt5 构建的轻量级图形化工具，旨在帮助用户快速、高效地对本地图像文件进行分类标注，特别适用于机器学习和数据集准备工作。

---

## 📸 应用截图


![PixClassify Screenshot/Demo](https://i.imgur.com/xO1y8mj.png)

---

## ✨ 核心功能

* **🎨 直观的图形界面**：简洁明了的界面设计，无需学习成本即可上手。
* **⚙️ 灵活配置**：启动时自由设置图片源路径、输出路径及自定义类别，并自动保存配置供下次使用。
* **🖼️ 多格式支持**：支持 `.png`, `.jpg`, `.jpeg`, `.bmp` 等主流图像格式。
* **👀 上下文预览**：同时展示上一张、当前和后两张图片，方便在分类时进行上下文比对，确保标注一致性。
* **⚡️ 高效标注操作**：
    * 支持 **鼠标点击** 或 **数字快捷键 (1-9)** 进行快速分类。
    * 分类后自动跳转到下一张未分类图片，操作流程不间断。
* **↔️ 便捷导航**：
    * 使用 `←` / `→` 箭头或按钮切换图片。
    * 通过左侧文件列表直接跳转到任意图片。
* **dynamic: 动态添加类别**：在标注过程中，可随时一键添加新的分类。
* **↩️ 撤销操作**：支持通过按钮或快捷键 (`Ctrl+Z`) 轻松撤销上一次的分类动作。
* **🖱️ 图像缩放**：按住 `Ctrl` 并滚动鼠标滚轮，可对当前主图像进行缩放查看细节。
* **🔄 断点续标**：程序自动加载已有分类进度，您可以随时关闭并从上次中断的地方继续工作。
* **📋 日志记录**：可选的详细操作日志，便于追踪和审计标注过程。

---

## 🛠️ 安装与启动

### 1. 环境准备
确保您的电脑已安装 Python 3。

### 2. 克隆项目并安装依赖
```bash
# 克隆项目 (如果您通过git管理)
git clone [https://github.com/SeanWong17/PixClassify.git](https://github.com/SeanWong17/PixClassify.git)
cd QuickLabel

# 安装必要的依赖库
pip install PyQt5
```

### 3. 运行程序
```bash
python main.py
```

---

## 📖 使用指南

1.  **初始设置**：
    * 首次运行，程序会弹出“参数设置”对话框。
    * **待分类图像路径**：选择包含所有待分类图片的文件夹。
    * **分类后保存路径**：选择一个用于存放分类结果的文件夹。程序会自动在此路径下根据类别名称创建子文件夹。
    * **类别名称**：输入所有预设的类别，用 **单个空格** 分隔（例如：`cat dog other`）。
    * 点击“确定”，配置将被保存，主窗口将启动。

2.  **进行标注**：
    * **主视图**：界面中央带蓝色边框的为当前待处理的图片。
    * **分类**：点击底部的类别按钮，或按下对应的数字键（`1` 对应第一个类别，`2` 对应第二个，以此类推），图片将被复制到目标文件夹，并自动切换到下一张。
    * **导航**：使用键盘 `←` 和 `→` 键或界面按钮在所有图片间自由导航。
    * **撤销**：若分类错误，按 `Ctrl+Z` 即可撤销上一步操作。
    * **跳转**：点击左侧列表中的文件名，可直接跳转到该图片进行查看或重新分类。

---

## ⌨️ 快捷键总览

| 快捷键             | 功能                         |
| ------------------ | ---------------------------- |
| `←` (左箭头)         | 查看上一张图片               |
| `→` (右箭头)         | 查看下一张图片               |
| `1`, `2`, ... `9`  | 将图片分到第 1, 2, ... 9个类别 |
| `Ctrl` + `Z`       | 撤销上一次的分类操作         |
| `Ctrl` + `鼠标滚轮`  | 缩放当前主图像               |

---

## 🔬 工作原理

* **文件安全**：本工具通过 **复制 (`shutil.copy2`)** 的方式进行文件归类，**绝不会修改或删除您的任何原始图片**，确保源数据安全。
* **状态恢复**：程序启动时会扫描输出目录，通过检查文件是否存在于类别子文件夹中来恢复已有的标注进度，实现断点续标。
* **配置持久化**：用户的路径和类别设置会被保存在一个本地配置文件中，下次启动时自动加载，免去重复输入的麻烦。

---

## 🙌 贡献

欢迎任何形式的贡献！如果您有好的建议或发现了Bug，请随时提交 [Issues](https://github.com/SeanWong17/PixClassify/issues) 或 [Pull Requests](https://github.com/SeanWong17/PixClassify/pulls)。

1.  Fork 本仓库
2.  创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  开启一个 Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

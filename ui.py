import sys
import resources
import os

import io
import weakref
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QTextEdit, QPushButton, QGroupBox, QLineEdit, QRadioButton,
                             QButtonGroup, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QDateTime, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon, QImage

from generate_prompt import gen_prompt
from doubao_generate_img import generate_img
from add_logo import add_logo_to_poster, remove_watermark


# 工作线程类
class WorkerThread(QThread):
    # 创建一个名为finished的信号对象，此信号没有携带额外的数据。
    # 通常用于在某个任务完成时进行通知，比如某个长时间运行的操作结束时，
    # 可以发射这个信号，连接到这个信号的槽函数会被调用。
    finished = pyqtSignal()
    # 创建一个名为progress的信号对象，该信号携带一个字符串类型的数据。
    # 常用于在任务执行过程中，传递进度相关的信息，例如进度百分比的字符串描述，
    # 如"50%"，以便连接到这个信号的槽函数能够根据这些信息更新进度显示等。
    progress = pyqtSignal(str)
    # 定义一个名为update_input的信号（Signal），它属于pyqtSignal类型。
    # 该信号用于在PyQt应用程序中进行对象间的事件通信。
    # 这里的信号update_input在发射时会携带一个字符串类型（str）的数据。
    # 通常在应用程序的某个特定事件发生时，会发射这个信号，
    # 而其他连接到这个信号的槽函数（slot function）可以接收到这个携带的字符串数据并进行相应处理。
    update_input = pyqtSignal(str)
    show_message_box = pyqtSignal(str)
    show_dialog = pyqtSignal(list)

    def __init__(self, task_type, data=None):
        super().__init__()
        self.task_type = task_type
        self.data = data

    def run(self):
        try:
            if self.task_type == "generate_plan":
                self._generate_plan()
            elif self.task_type == "generate_poster":
                self._generate_poster()
        except Exception as e:
            self.progress.emit(f"错误: {str(e)}")
        finally:
            self.finished.emit()

    def _generate_plan(self):
        """模拟生成方案的耗时任务"""

        for i in gen_prompt(self.data):
            self.update_input.emit(i)

    def _generate_poster(self):
        """模拟生成海报的耗时任务"""
        if not self.data:
            self.progress.emit("错误: 缺少必要的输入数据")
            return

        self.progress.emit("开始生成海报...")
        for i in generate_img(self.data):
            if type(i) == list:
                self.show_dialog.emit(i)
                continue
            if i == "二维码生成完毕！":
                self.show_message_box.emit("扫码二维码进行授权！")

            self.progress.emit(f"{i}")

        self.progress.emit(f"海报生成完成!")


class PosterGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 启用高DPI缩放
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self.setWindowTitle("AI 海报生成器 - version 25.06.05")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)  # 启用最大化按钮
        self.setWindowIcon(QIcon(":/tb.png"))  # 设置窗口图标

        # 初始化UI后再调整窗口大小
        self.initUI()
        self.adjustWindowSize()

        # 工作线程
        self.worker_thread = None

        #
        self.render_md = ''

    def adjustWindowSize(self):
        """根据屏幕尺寸和缩放比例自动调整窗口大小"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        # 计算基于屏幕尺寸的窗口大小 (占据屏幕宽高的60%-80%)
        width = int(screen_rect.width() * 0.65)
        height = int(screen_rect.height() * 0.85)

        # 设置最小尺寸限制
        min_width = int(screen_rect.width() * 0.3)
        min_height = int(screen_rect.height() * 0.8)

        self.resize(width, height)
        self.setMinimumSize(min_width, min_height)

        # 居中显示窗口
        self.move(
            (screen_rect.width() - width) // 2,
            (screen_rect.height() - height) // 2
        )

    def initUI(self):
        # 主窗口部件
        main_widget = QWidget()

        self.setCentralWidget(main_widget)

        # 获取系统DPI缩放比例
        screen = QApplication.primaryScreen()
        logical_dpi = screen.logicalDotsPerInch()
        scale_factor = max(1.0, logical_dpi / 96.0)  # 确保最小缩放为1.0

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(int(20 * scale_factor),
                                       int(20 * scale_factor),
                                       int(20 * scale_factor),
                                       int(20 * scale_factor))
        main_layout.setSpacing(int(15 * scale_factor))
        main_widget.setLayout(main_layout)

        # 关键词输入区域 (新增)
        # 创建一个名为“关键词设置”的QGroupBox对象，并将其赋值给keyword_group变量
        keyword_group = QGroupBox("关键词设置")
        # 创建一个水平布局对象QHBoxLayout，并将其赋值给keyword_layout变量
        keyword_layout = QHBoxLayout()

        # 创建一个QLabel对象，显示文本“指定海报关键词:”，并赋值给self.keyword_label变量
        self.keyword_label = QLabel("指定海报关键词:")
        # 设置self.keyword_label的字体为“Microsoft YaHei”，字号根据scale_factor动态调整为12乘以scale_factor
        self.keyword_label.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        # 创建一个QLineEdit对象，用于用户输入内容，赋值给self.keyword_input变量
        self.keyword_input = QLineEdit()
        # 设置self.keyword_input的占位文本为“请输入海报关键词”，提示用户输入
        self.keyword_input.setPlaceholderText("请输入海报关键词")
        # 设置self.keyword_input的字体为“Microsoft YaHei”，字号根据scale_factor动态调整为8乘以scale_factor
        self.keyword_input.setFont(QFont("Microsoft YaHei", int(8 * scale_factor)))

        # 将self.keyword_label添加到keyword_layout布局中
        keyword_layout.addWidget(self.keyword_label)
        # 将self.keyword_input添加到keyword_layout布局中
        keyword_layout.addWidget(self.keyword_input)
        # 将keyword_layout布局设置给keyword_group，完成布局设置
        keyword_group.setLayout(keyword_layout)

        # 输入区域
        input_group = QGroupBox("内容输入")
        input_layout = QHBoxLayout()  # 使用水平布局
        input_layout.setSpacing(int(10 * scale_factor))
        # 思考过程输入框的垂直布局
        thought_layout = QVBoxLayout()
        thought_label = QLabel("AI 思考过程:")
        thought_label.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        self.thought_input = QTextEdit()
        self.thought_input.setPlaceholderText("在此输入AI生成的内容...")
        self.thought_input.setMinimumHeight(int(160 * scale_factor))
        thought_layout.addWidget(thought_label)

        thought_layout.addWidget(self.thought_input)
        # 具体方案输入框的垂直布局
        plan_layout = QVBoxLayout()
        plan_label = QLabel("具体方案（可根据需求进行修改）:")
        plan_label.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        self.plan_input = QTextEdit()
        self.plan_input.setPlaceholderText("在此输入具体方案...")
        self.plan_input.setMinimumHeight(int(160 * scale_factor))
        plan_layout.addWidget(plan_label)

        plan_layout.addWidget(self.plan_input)
        # 将两个垂直布局添加到水平布局中
        input_layout.addLayout(thought_layout)
        input_layout.addLayout(plan_layout)
        input_group.setLayout(input_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(int(15 * scale_factor))
        button_layout.setContentsMargins(0, int(10 * scale_factor), 0, int(10 * scale_factor))

        self.generate_plan_btn = QPushButton("生成方案")
        self.generate_poster_btn = QPushButton("生成海报")

        # 设置按钮字体大小
        button_font = QFont("Microsoft YaHei", int(12 * scale_factor))
        button_font.setBold(True)
        self.generate_plan_btn.setFont(button_font)
        self.generate_poster_btn.setFont(button_font)

        # 设置按钮最小尺寸
        btn_min_size = QSize(int(120 * scale_factor), int(40 * scale_factor))
        self.generate_plan_btn.setMinimumSize(btn_min_size)
        self.generate_poster_btn.setMinimumSize(btn_min_size)

        # 创建文字标签
        quantity_label = QLabel("选择海报生成数量:")
        quantity_label.setFont(QFont("Microsoft YaHei", int(12 * scale_factor)))
        quantity_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        button_layout.addWidget(quantity_label)

        # 创建单选按钮组用于管理单选按钮
        self.quantity_group = QButtonGroup(self)
        self.quantity_group.setExclusive(True)  # 确保互斥选择
        # 定义可用数量选项
        quantities = [2, 4, 6, 8]
        for qty in quantities:
            if qty == 2:
                tips = "(极速)"
            elif qty == 4:
                tips = "(快速)"
            elif qty == 8:
                tips = "(慢速)"
            else:
                tips = "(标准)"
            radio_btn = QRadioButton(f"{qty}张" + tips)
            radio_btn.setFont(QFont("Microsoft YaHei", int(10 * scale_factor)))
            radio_btn.setProperty("quantity", qty)  # 存储数值属性
            button_layout.addWidget(radio_btn)
            self.quantity_group.addButton(radio_btn)

        # 默认选中第一个按钮
        if self.quantity_group.buttons():
            self.quantity_group.buttons()[0].setChecked(True)

        # 添加伸缩空间使按钮居中
        button_layout.addStretch()
        button_layout.addWidget(self.generate_plan_btn)
        button_layout.addWidget(self.generate_poster_btn)
        button_layout.addStretch()

        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("操作日志将显示在这里...")
        self.log_output.setMinimumHeight(int(180 * scale_factor))

        # 设置日志区域的字体
        log_font = QFont("Consolas", int(11 * scale_factor))
        self.log_output.setFont(log_font)

        # 直接添加QTextEdit到布局，不再使用QScrollArea
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)

        # 将所有部件添加到主布局

        main_layout.addWidget(input_group)
        main_layout.addWidget(keyword_group)  # 新增关键词区域
        main_layout.addLayout(button_layout)
        main_layout.addWidget(log_group)

        # 连接按钮信号
        self.generate_plan_btn.clicked.connect(self.generate_plan)
        self.generate_poster_btn.clicked.connect(self.generate_poster)

        # 动态样式表
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #f5f7fa;
            }}
            QGroupBox {{
                font: bold {int(14 * scale_factor)}px 'Microsoft YaHei';
                border: {int(1 * scale_factor)}px solid #d1d5db;
                border-radius: {int(6 * scale_factor)}px;
                margin-top: {int(10 * scale_factor)}px;
                padding-top: {int(15 * scale_factor)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {int(10 * scale_factor)}px;
                padding: 0 {int(3 * scale_factor)}px;
            }}
            QTextEdit {{
                font: {int(15 * scale_factor)}px 'Microsoft YaHei';
                border: {int(1 * scale_factor)}px solid #d1d5db;
                border-radius: {int(4 * scale_factor)}px;
                padding: {int(8 * scale_factor)}px;
                background-color: white;
            }}
            QPushButton {{
                font: bold {int(14 * scale_factor)}px 'Microsoft YaHei';
                background-color: #4f46e5;
                color: white;
                border: none;
                border-radius: {int(6 * scale_factor)}px;
                padding: {int(10 * scale_factor)}px {int(20 * scale_factor)}px;
                min-width: {int(120 * scale_factor)}px;
            }}
            QPushButton:hover {{
                background-color: #4338ca;
            }}
            QPushButton:pressed {{
                background-color: #3730a3;
            }}
            QLabel {{
                font: {int(13 * scale_factor)}px 'Microsoft YaHei';
                color: #374151;
            }}
             QLineEdit {{
                padding: {int(8 * scale_factor)}px;  /* 统一内边距 */
                /* 或者分别设置四个方向的内边距 */
                padding-left: {int(12 * scale_factor)}px;
                padding-right: {int(12 * scale_factor)}px;
                padding-top: {int(8 * scale_factor)}px;
                padding-bottom: {int(8 * scale_factor)}px;
            }}
        """)

    def generate_plan(self):
        """生成方案 - 使用线程执行耗时任务"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.log("警告: 已有任务正在运行，请等待完成")
            return

        if self.keyword_input.text() == '':
            self.keyword_input.setPlaceholderText("关键词不能为空")
            self.log("警告: 请输入关键词")
            return

        self.log(f"开始生成方案「{self.keyword_input.text()}」")

        # 禁用按钮防止重复点击
        self.generate_plan_btn.setEnabled(False)
        self.generate_poster_btn.setEnabled(False)
        self.generate_plan_btn.setText('等待方案生成...')
        self.generate_poster_btn.setText("等待方案生成...")
        # 清空两个输入框
        self.thought_input.clear()
        self.plan_input.clear()

        # 清空 render_md 字符串
        self.render_md = ''

        # 创建并启动工作线程
        # 这里假设WorkerThread类在其他地方定义，并且接受一个字符串参数用于某种任务标识
        keyword_input_text = self.keyword_input.text()
        self.worker_thread = WorkerThread("generate_plan", keyword_input_text)
        # 意味着当worker_thread线程在执行过程中发出progress信号时，会调用self.log方法
        self.worker_thread.progress.connect(self.log)
        # 当worker_thread线程执行完成时，会发出finished信号，进而调用self.on_task_finished方法
        self.worker_thread.finished.connect(self.on_task_finished)
        self.worker_thread.update_input.connect(self.update_thought_input)
        # 启动worker_thread线程，开始执行该线程中的任务
        self.worker_thread.start()

    def generate_poster(self):
        """生成海报 - 使用线程执行耗时任务"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.log("警告: 已有任务正在运行，请等待完成")
            return

        # 获取输入数据
        plan = self.plan_input.toPlainText()
        # 获取要生成海报的数量
        for button in self.quantity_group.buttons():
            if button.isChecked():
                number_img = button.property("quantity")  # 返回 int 类型数值

        if not plan:
            self.log("× 错误: 具体方案不能为空!")
            return
        plan = f"帮我生成{number_img}张海报：" + plan.replace('军徽', '').replace('领袖', '').replace('军旗',
                                                                                                     '').replace('徽章',
                                                                                                                 '')
        # 禁用按钮防止重复点击
        self.generate_plan_btn.setEnabled(False)
        self.generate_poster_btn.setEnabled(False)
        self.generate_plan_btn.setText('海报正在生成...')
        self.generate_poster_btn.setText("海报正在生成...")

        # 创建并启动工作线程
        self.worker_thread = WorkerThread("generate_poster", {"prompt": plan, 'img_num': number_img})
        self.worker_thread.progress.connect(self.log)
        self.worker_thread.finished.connect(self.on_task_finished)
        self.worker_thread.show_message_box.connect(self.show_message_box)
        self.worker_thread.show_dialog.connect(self.show_dialog)
        self.worker_thread.start()

    def show_dialog(self, content_list):
        """显示窗口，添加三个单选框，用于选择图片"""
        try:
            page_number = 0
            for img in content_list:
                page_number += 1
                # 创建对话框
                dialog = QDialog(self)
                dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 移除问号按钮
                dialog.setWindowTitle(f'第{page_number}张海报 - 选择logo')
                dialog.setWindowModality(Qt.ApplicationModal)
                dialog.setAttribute(Qt.WA_DeleteOnClose)  # 关闭时自动删除

                # 主布局
                main_layout = QVBoxLayout(dialog)

                # 图片预览
                # img_array 是一个 NumPy 数组
                img_array = remove_watermark(img['content'])

                # 转换为 QImage
                height, width, channel = img_array.shape
                bytes_per_line = 3 * width
                qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)

                # 转换为 QPixmap
                pixmap = QPixmap.fromImage(qimage)
                image_label = QLabel(dialog)
                # 图片容器布局，添加边距
                image_container = QWidget()
                image_layout = QVBoxLayout(image_container)
                # image_layout.setContentsMargins()
                image_layout.addWidget(image_label)
                main_layout.addWidget(image_container)

                def update_poster(pixmap):
                    # 保持原始宽高比，设置最大尺寸
                    max_size = QSize(1280, 720)  # 可根据需要调整最大尺寸
                    if pixmap.width() > max_size.width() or pixmap.height() > max_size.height():
                        pixmap = pixmap.scaled(max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_label.setPixmap(pixmap)
                    image_label.setAlignment(Qt.AlignCenter)

                update_poster(pixmap)  # 加载图片

                # 创建单选按钮组
                self.radio_group = QButtonGroup(dialog)
                t_list = ['原图', '白色logo', '黑色logo']

                # 按钮布局
                radio_layout = QHBoxLayout()
                radio_layout.setSpacing(20)  # 设置按钮间距为20像素
                radio_layout.setAlignment(Qt.AlignCenter)
                for i in range(1, 4):
                    radio = QRadioButton(t_list[i - 1], dialog)
                    radio.setFont(QFont("Microsoft YaHei", 10))
                    self.radio_group.addButton(radio, i)
                    radio_layout.addWidget(radio)
                main_layout.addLayout(radio_layout)

                # 定义处理函数
                def handle_radio_selection(button):
                    """处理单选按钮选择事件"""
                    selected_id = self.radio_group.checkedId()
                    selected_text = button.text()
                    self.log(f"选择了: {selected_text} (ID: {selected_id})")
                    poster = add_logo_to_poster(pixmap, selected_id, logo_size=0.7)

                    # 将PIlmage对象转换为QPixmap对象
                    byte_array = io.BytesIO()
                    poster.save(byte_array, format='PNG')  # 保存为PNG格式的字节流
                    byte_array = byte_array.getvalue()  # 获取字节数据

                    # 通过QImage加载字节数据
                    qimage = QImage()
                    qimage.loadFromData(byte_array)  # 自动识别格式

                    # 转换为QPixmap
                    self.poster_qt = QPixmap.fromImage(qimage)

                    # 将添加loog的海报显示在标签上
                    update_poster(self.poster_qt)

                # 连接单选按钮点击信号
                self.radio_group.buttonClicked.connect(handle_radio_selection)

                # 添加确认按钮
                btn_confirm = QPushButton("保存图片", dialog)
                btn_confirm.setFont(QFont("Microsoft YaHei", 10))
                btn_confirm.setFixedWidth(60)  # 设置按钮宽度

                # 按钮容器布局
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(50, 10, 50, 20)
                btn_layout.addWidget(btn_confirm)
                main_layout.addWidget(btn_container)

                # 使用weakref避免内存泄漏
                weak_dialog = weakref.ref(dialog)

                def on_confirm():
                    d = weak_dialog()
                    if d:
                        selected_id = self.radio_group.checkedId()
                        if selected_id == -1:
                            QMessageBox.warning(d, "警告", "请先选择一个图片选项!")
                            return
                        self.log(f"用户选择了 {t_list[selected_id - 1]}")
                        # 2. 检查对象是否有效
                        if not self.poster_qt.isNull():
                            # 3. 保存到本地（支持PNG/JPEG/BMP等格式）
                            success = self.poster_qt.save(img['path'])  # 保存海报

                            # 可选：验证保存结果
                            if success:
                                self.log(f"图片已保存至: {img['path']}")
                                os.startfile(img['path'])
                            else:
                                self.log("保存失败！请检查路径和权限")
                        else:
                            self.log("对象为空，无法保存")
                        d.accept()

                btn_confirm.clicked.connect(on_confirm)

                def get_dialog_size_limits():
                    """根据屏幕尺寸计算对话框尺寸边界"""
                    screen = QApplication.primaryScreen().availableGeometry()

                    # 计算最大尺寸（屏幕尺寸的80%）
                    max_width = int(screen.width() * 0.8)
                    max_height = int(screen.height() * 0.8)

                    # 计算最小尺寸（屏幕尺寸的30%）
                    min_width = int(screen.width() * 0.3)
                    min_height = int(screen.height() * 0.3)

                    # 确保最小尺寸不小于400×400
                    min_width = max(400, min_width)
                    min_height = max(400, min_height)

                    return QSize(max_width, max_height), QSize(min_width, min_height)

                """显示自适应尺寸的对话框"""
                # 1. 获取屏幕信息
                screen = QApplication.primaryScreen().availableGeometry()

                # 2. 计算动态尺寸边界
                max_size, min_size = get_dialog_size_limits()

                # 3. 根据内容自适应调整
                dialog.adjustSize()
                dialog_size = dialog.size()

                # 4. 边界检查与尺寸调整
                if (dialog_size.width() > max_size.width() or
                        dialog_size.height() > max_size.height()):
                    # 保持宽高比缩放
                    scaled_size = dialog_size.scaled(max_size, Qt.KeepAspectRatio)
                    dialog.resize(scaled_size)
                elif (dialog_size.width() < min_size.width() or
                      dialog_size.height() < min_size.height()):
                    dialog.resize(min_size)
                else:
                    # 保持自适应尺寸
                    dialog.resize(dialog_size)

                # 5. 确保对话框在屏幕内居中显示
                dialog.move(
                    screen.left() + (screen.width() - dialog.width()) // 2,
                    screen.top() + (screen.height() - dialog.height()) // 2
                )

                # 6. 显示对话框
                dialog.exec_()

        except Exception as e:
            self.log(f"对话框错误: {str(e)}")
            print(e)
            import traceback
            traceback.print_exc()

    def show_message_box(self, message):
        """显示消息框"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("提示：")
        msg_box.setText("请使用豆包APP扫码二维码进行授权:")
        # 使用样式表设置字体大小
        msg_box.setStyleSheet("""
                QLabel {
                    font-size: 40px;  /* 设置文本大小 */
                    font-weight: bold;  /* 可选：加粗 */
                    color: red;  /* 可选：设置文本颜色 */
                }
                
            """)

        # 加载图片并设置
        pixmap = QPixmap("decoded_image.jpg")  # 替换为你的图片路径
        msg_box.setIconPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))  # 调整大小
        # 设置按钮（默认是 "OK"）
        msg_box.setStandardButtons(QMessageBox.Ok)  # 确保只显示 "OK" 按钮
        ok_button = msg_box.button(QMessageBox.Ok)  # 获取 "OK" 按钮
        ok_button.setText("已扫描完毕！")  # 修改文本为 "已扫描完毕！"
        result = msg_box.exec_()  # 这会阻塞直到用户响应
        if result == 1024:
            self.log('已成功授权，请重新点击授权按钮')
            os.remove('decoded_image.jpg')

    def update_thought_input(self, text):
        """更新 thought_input 文本框内容"""

        prompt = self.thought_input.toPlainText()
        if '</think>\n\n' in prompt:
            self.render_md += text
            self.plan_input.setMarkdown(self.render_md)

            # 获取文本光标并移动到底部
            cursor = self.plan_input.textCursor()
            cursor.movePosition(cursor.End)
            self.plan_input.setTextCursor(cursor)

            # 使光标在当前显示区域内可见，方便用户进行输入操作
            self.plan_input.ensureCursorVisible()
        else:
            # 将文本（text）添加到thought_input输入框中
            self.thought_input.insertPlainText(text)
            # 这通常用于保证用户输入内容后，光标能正常显示在合适位置，方便继续输入
            self.thought_input.ensureCursorVisible()

    def on_task_finished(self):
        """任务完成后的回调"""
        self.generate_plan_btn.setEnabled(True)
        self.generate_poster_btn.setEnabled(True)
        self.generate_plan_btn.setText("生成方案")
        self.generate_poster_btn.setText("生成海报")
        self.worker_thread = None
        self.log("任务已完成，按钮已重新启用")

    def log(self, message):
        """线程安全的日志记录"""
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        # 使用 QMetaObject.invokeMethod 确保线程安全
        self.log_output.append(f"[{current_time}] > {message}")
        # 获取文本光标并移动到底部
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.End)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()


if __name__ == "__main__":
    # 启用高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    window = PosterGeneratorApp()
    window.show()
    sys.exit(app.exec_())

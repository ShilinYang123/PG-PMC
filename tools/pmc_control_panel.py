import sys
import os
import subprocess
import threading
import time
import webbrowser
import queue
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import qRegisterMetaType

class PMCControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        qRegisterMetaType('QTextCursor')
        self.setWindowTitle("PMC智能生产管理控制面板 - BD300项目")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)

        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.log_queue = queue.Queue()
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.process_log_queue)
        self.log_timer.start(500)

        self.init_ui()

    def process_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                self.status_text.append(f"[{timestamp}] {message}")
        except queue.Empty:
            pass

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Title frame
        title_frame = QFrame()
        title_frame.setFixedHeight(80)
        title_frame.setStyleSheet("background-color: #2c3e50;")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("PMC智能生产管理控制面板")
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title_label.setStyleSheet("color: #ecf0f1;")
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("BD300项目PMC控制系统 - 集成操作界面")
        subtitle_label.setFont(QFont('Microsoft YaHei', 10))
        subtitle_label.setStyleSheet("color: #ecf0f1;")
        title_layout.addWidget(subtitle_label)

        main_layout.addWidget(title_frame)

        # Main content
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 5, 10, 10)

        # Left panel
        left_panel = QScrollArea()
        left_panel.setWidgetResizable(True)
        left_panel.setFixedWidth(320)
        left_panel.setStyleSheet("background-color: #f0f0f0;")
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setAlignment(Qt.AlignTop)

        self.setup_control_panel(left_layout)
        left_panel.setWidget(left_content)
        content_layout.addWidget(left_panel)

        # Right panel
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("background-color: #ffffff; border: none;")
        content_layout.addWidget(self.status_text)

        main_layout.addWidget(content_widget)

        self.log_message("系统初始化完成。")
        self.log_message("欢迎使用PMC控制面板！")

    def setup_control_panel(self, layout):
        # System Status
        status_label = QLabel("🔍 系统状态")
        status_label.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        layout.addWidget(status_label)

        self.system_status = QLabel("当前状态: 正常")
        self.system_status.setFont(QFont('Microsoft YaHei', 9))
        layout.addWidget(self.system_status)

        self.last_check_time = QLabel("最后检查: " + time.strftime('%Y-%m-%d %H:%M:%S'))
        self.last_check_time.setFont(QFont('Microsoft YaHei', 9))
        layout.addWidget(self.last_check_time)

        layout.addSpacing(10)

        # Quick Operations
        quick_label = QLabel("🚀 快速操作")
        quick_label.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        layout.addWidget(quick_label)

        check_btn = QPushButton("🌅 执行早上启动检查")
        check_btn.setFont(QFont('Microsoft YaHei', 9))
        check_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        check_btn.clicked.connect(self.run_startup_check)
        layout.addWidget(check_btn)

        status_btn = QPushButton("📋 查看详细状态")
        status_btn.setFont(QFont('Microsoft YaHei', 9))
        status_btn.setStyleSheet("background-color: #2ecc71; color: white; padding: 8px;")
        status_btn.clicked.connect(self.view_system_status)
        layout.addWidget(status_btn)

        layout.addSpacing(10)

        # System Launch
        launch_label = QLabel("🎯 系统启动")
        launch_label.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        layout.addWidget(launch_label)

        mgmt_btn = QPushButton("🎯 启动PMC管理系统")
        mgmt_btn.setFont(QFont('Microsoft YaHei', 9))
        mgmt_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px;")
        mgmt_btn.clicked.connect(self.launch_management_system)
        layout.addWidget(mgmt_btn)

        track_btn = QPushButton("📊 启动PMC追踪系统")
        track_btn.setFont(QFont('Microsoft YaHei', 9))
        track_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px;")
        track_btn.clicked.connect(self.launch_tracking_system)
        layout.addWidget(track_btn)

        layout.addSpacing(10)

        # System Tools
        tools_label = QLabel("🔧 系统工具")
        tools_label.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        layout.addWidget(tools_label)

        struct_btn = QPushButton("🔍 执行结构检查")
        struct_btn.setFont(QFont('Microsoft YaHei', 9))
        struct_btn.setStyleSheet("background-color: #f39c12; color: white; padding: 8px;")
        struct_btn.clicked.connect(self.run_structure_check)
        layout.addWidget(struct_btn)

        docs_btn = QPushButton("📚 打开项目文档")
        docs_btn.setFont(QFont('Microsoft YaHei', 9))
        docs_btn.setStyleSheet("background-color: #34495e; color: white; padding: 8px;")
        docs_btn.clicked.connect(self.open_docs)
        layout.addWidget(docs_btn)

        manual_btn = QPushButton("📖 快速操作手册")
        manual_btn.setFont(QFont('Microsoft YaHei', 9))
        manual_btn.setStyleSheet("background-color: #16a085; color: white; padding: 8px;")
        manual_btn.clicked.connect(self.open_manual)
        layout.addWidget(manual_btn)

    def log_message_direct(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.status_text.append(f"[{timestamp}] {message}")

    def run_command_async(self, command, description):
        def target():
            self.log_message(f"开始{description}...")
            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
                while True:
                    output = process.stdout.readline()
                    if output:
                        self.log_message(output.strip())
                    if process.poll() is not None:
                        break
                if process.returncode == 0:
                    self.log_message(f"{description}完成。")
                else:
                    self.log_message(f"{description}失败（代码: {process.returncode}）。")
            except Exception as e:
                self.log_message(f"执行错误: {str(e)}")

        thread = threading.Thread(target=target)
        thread.start()

    def run_startup_check(self):
        cmd = ['python', os.path.join(self.project_root, 'tools', 'startup_check.py')]
        self.run_command_async(cmd, "早上启动检查")

    def view_system_status(self):
        self.log_message("查看详细系统状态...")
        self.log_message("系统状态: 正常")

    def launch_management_system(self):
        cmd = ['python', os.path.join(self.project_root, 'project', 'pmc_management_system.py')]
        self.run_command_async(cmd, "PMC管理系统")

    def launch_tracking_system(self):
        cmd = ['python', os.path.join(self.project_root, 'project', 'pmc_tracking_system.py')]
        self.run_command_async(cmd, "PMC追踪系统")

    def run_structure_check(self):
        cmd = ['python', os.path.join(self.project_root, 'tools', 'structure_check.py')]
        self.run_command_async(cmd, "结构检查")

    def open_docs(self):
        docs_path = os.path.join(self.project_root, 'docs')
        webbrowser.open(docs_path)
        self.log_message("打开项目文档文件夹。")

    def open_manual(self):
        manual_path = os.path.join(self.project_root, 'docs', '快速操作手册.md')
        if os.path.exists(manual_path):
            webbrowser.open(manual_path)
            self.log_message("打开快速操作手册。")
        else:
            self.log_message("快速操作手册未找到。")

if __name__ == '__main__':
    try:
        print("正在启动PMC控制面板...")
        print(f"Python版本: {sys.version}")
        
        # 检查显示环境
        import os
        if os.name == 'nt':  # Windows
            print("Windows环境检测")
            # 检查是否在远程桌面或无显示环境
            if 'SESSIONNAME' in os.environ:
                session = os.environ.get('SESSIONNAME', '')
                print(f"会话类型: {session}")
                if session.startswith('RDP-'):
                    print("检测到远程桌面环境")
        
        # 设置Qt平台插件
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        
        app = QApplication(sys.argv)
        print("QApplication已创建")
        
        # 检查是否有可用的显示
        try:
            from PyQt5.QtWidgets import QDesktopWidget
            desktop = QDesktopWidget()
            screen_count = desktop.screenCount()
            print(f"屏幕数量: {screen_count}")
            if screen_count > 0:
                print(f"主屏幕尺寸: {desktop.screenGeometry()}")
            else:
                print("警告: 未检测到可用屏幕")
        except Exception as e:
            print(f"屏幕检测失败: {e}")
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#ecf0f1'))
        app.setPalette(palette)
        print("正在创建主窗口...")
        
        window = PMCControlPanel()
        print("主窗口已创建，正在显示...")
        
        # 设置窗口属性
        window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
        window.show()
        window.raise_()
        window.activateWindow()
        print("窗口已显示，进入事件循环...")
        
        # 确保窗口可见
        app.processEvents()
        
        # 启动事件循环
        exit_code = app.exec_()
        print(f"应用程序退出，代码: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 如果是显示相关错误，提供解决方案
        error_str = str(e).lower()
        if 'display' in error_str or 'screen' in error_str or 'qt' in error_str:
            print("\n解决方案:")
            print("1. 确保在有图形界面的环境中运行")
            print("2. 如果使用远程桌面，请确保允许GUI应用")
            print("3. 尝试在本地桌面环境中运行")
        
        sys.exit(1)
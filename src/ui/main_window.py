"""
Main Application Window
Features:
- Screen-adaptive sizing (occupies ~82% of screen resolution, centered)
- Fluent Design styling & auto/toggle theme support
- Smooth vertical scroll container: Area 1 occupies primary viewport, scroll down for Area 2
"""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
)
from qfluentwidgets import (
    SmoothScrollArea, setTheme, Theme, isDarkTheme,
    Action, RoundMenu, FluentIcon, ToolButton, TransparentToolButton,
    TitleLabel, CaptionLabel, InfoBar, InfoBarPosition
)

from src.config import APP_NAME_CN, APP_NAME_EN, APP_VERSION
from src.ui.module1.module1_widget import Module1Widget
from src.ui.module2.module2_widget import Module2Widget


class MainWindow(QMainWindow):
    """
    主程序窗口
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME_CN} - {APP_NAME_EN} v{APP_VERSION}")

        self._adapt_screen_size()
        self._init_ui()

    def _adapt_screen_size(self):
        """自适应当前屏幕分辨率，确保拥有足够大的操作视窗空间"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            avail_geo = screen.availableGeometry()
            # 占据可用屏幕的 82% 宽与 86% 高
            target_width = max(1120, int(avail_geo.width() * 0.82))
            target_height = max(720, int(avail_geo.height() * 0.86))
            
            # 居中放置
            x = avail_geo.x() + (avail_geo.width() - target_width) // 2
            y = avail_geo.y() + (avail_geo.height() - target_height) // 2

            self.setGeometry(x, y, target_width, target_height)
        else:
            self.resize(1200, 800)

        self.setMinimumSize(980, 640)

    def _init_ui(self):
        # 主中心部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(10)

        # 顶部工具栏与标题
        header_bar = QHBoxLayout()
        header_bar.setSpacing(12)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        app_title = TitleLabel(APP_NAME_CN)
        app_title.setStyleSheet("font-size: 20px; font-weight: 700;")
        app_subtitle = CaptionLabel(f"{APP_NAME_EN} · Windows 本地文件处理工具")
        app_subtitle.setStyleSheet("color: rgba(128, 128, 128, 0.8);")
        title_container.addWidget(app_title)
        title_container.addWidget(app_subtitle)
        header_bar.addLayout(title_container)

        header_bar.addStretch()

        # 主题切换按钮
        self.theme_btn = TransparentToolButton(FluentIcon.CONSTRACT, self)
        self.theme_btn.setToolTip("切换深色 / 浅色主题")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_bar.addWidget(self.theme_btn)

        # 帮助/关于按钮
        self.help_btn = TransparentToolButton(FluentIcon.INFO, self)
        self.help_btn.setToolTip("关于软件")
        self.help_btn.clicked.connect(self._show_about)
        header_bar.addWidget(self.help_btn)

        main_layout.addLayout(header_bar)

        # 核心滚动视窗：右侧带有现代平滑滚动条
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # 滚动容器内容部件
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 12, 16)
        self.content_layout.setSpacing(20)

        # 区域 1：模块 1（当前视区主区域）
        self.module1_widget = Module1Widget(self.content_widget)
        self.content_layout.addWidget(self.module1_widget)

        # 区域 2：模块 2（向下滑动呈现）
        self.module2_widget = Module2Widget(self.content_widget)
        self.content_layout.addWidget(self.module2_widget)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 保证区域1至少占据主视窗高度（减去标题栏与边距），使区域2位于第一屏下方，需要滚动条下滚展现
        viewport_height = self.scroll_area.viewport().height()
        if viewport_height > 200:
            self.module1_widget.setMinimumHeight(viewport_height - 10)

    def _toggle_theme(self):
        new_theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
        setTheme(new_theme)
        InfoBar.info(
            title="主题已切换",
            content=f"已切换为 {'浅色' if new_theme == Theme.LIGHT else '深色'} 模式",
            parent=self,
            duration=1500,
            position=InfoBarPosition.TOP_RIGHT
        )

    def _show_about(self):
        InfoBar.info(
            title="关于本软件",
            content=f"{APP_NAME_CN} ({APP_NAME_EN})\n版本: v{APP_VERSION}\n基于 PySide6 与 Fluent Design 架构",
            parent=self,
            duration=4000,
            position=InfoBarPosition.TOP_RIGHT
        )

"""
Main Application Window
Features:
- Screen-adaptive sizing (occupies ~82% of screen resolution, centered)
- Fluent Design styling & high-contrast Light/Dark theme support
- Top SegmentedWidget navigation driving:
  1. Aiarty Image Matting（抠图）- Workflow containing Module 1 + Transition Bar + Module 2
  2. Aiarty Image Enhancer（画质增强）- Extensible workspace placeholder
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
)
from qfluentwidgets import (
    setTheme, Theme, isDarkTheme, qconfig, SegmentedWidget,
    FluentIcon, TransparentToolButton, TitleLabel, CaptionLabel, InfoBar, InfoBarPosition
)

from src.config import APP_NAME_CN, APP_NAME_EN, APP_VERSION
from src.ui.theme_helper import apply_app_palette, get_window_qss
from src.ui.pages.matting_page import MattingWorkflowPage
from src.ui.pages.enhancer_page import EnhancerWorkflowPage


class MainWindow(QMainWindow):
    """
    主程序窗口
    """
    def __init__(self):
        super().__init__()
        self._current_route = "matting"
        self.setWindowTitle(f"{APP_NAME_CN} - {APP_NAME_EN} v{APP_VERSION}")

        self._adapt_screen_size()
        self._init_ui()

        # 监听全局主题变更，实时同步全套调色板与组件样式
        qconfig.themeChanged.connect(self._on_theme_changed)
        self._apply_theme_styling(isDarkTheme())

    def _adapt_screen_size(self):
        """自适应当前屏幕分辨率，确保拥有足够大的操作视窗空间"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            avail_geo = screen.availableGeometry()
            target_width = max(1120, int(avail_geo.width() * 0.82))
            target_height = max(720, int(avail_geo.height() * 0.86))

            x = avail_geo.x() + (avail_geo.width() - target_width) // 2
            y = avail_geo.y() + (avail_geo.height() - target_height) // 2

            self.setGeometry(x, y, target_width, target_height)
        else:
            self.resize(1200, 800)

        self.setMinimumSize(980, 640)

    def _init_ui(self):
        # 主中心部件
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(18, 14, 18, 18)
        main_layout.setSpacing(12)

        # 顶部工具栏与标题
        header_bar = QHBoxLayout()
        header_bar.setSpacing(12)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        self.app_title = TitleLabel(APP_NAME_CN, self.central_widget)
        self.app_title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.app_subtitle = CaptionLabel(f"{APP_NAME_EN} · Windows 本地文件处理工具", self.central_widget)
        title_container.addWidget(self.app_title)
        title_container.addWidget(self.app_subtitle)
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

        # 形态 A：顶部分段胶囊选项卡导航 (SegmentedWidget)
        nav_container = QHBoxLayout()
        self.segmented_nav = SegmentedWidget(self.central_widget)
        self.segmented_nav.setFixedHeight(36)
        self.segmented_nav.addItem(
            routeKey="matting",
            text="Aiarty Image Matting（抠图）",
            icon=FluentIcon.PHOTO
        )
        self.segmented_nav.addItem(
            routeKey="enhancer",
            text="Aiarty Image Enhancer（画质增强）",
            icon=FluentIcon.BRUSH
        )
        nav_container.addWidget(self.segmented_nav)
        nav_container.addStretch()
        main_layout.addLayout(nav_container)

        # 多选项卡内容容器 (QStackedWidget)
        self.stacked_widget = QStackedWidget(self.central_widget)

        # Tab 1: 抠图工作流页面（模块1+模块2）
        self.matting_page = MattingWorkflowPage(self.stacked_widget)
        self.stacked_widget.addWidget(self.matting_page)

        # Tab 2: 画质增强待接入页面
        self.enhancer_page = EnhancerWorkflowPage(self.stacked_widget)
        self.stacked_widget.addWidget(self.enhancer_page)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # 选项卡切换信号绑定
        self.segmented_nav.currentItemChanged.connect(self._on_tab_changed)
        self.segmented_nav.setCurrentItem("matting")

    # 便捷引用属性，向下兼容外部调用及测试代码
    @property
    def module1_widget(self):
        return self.matting_page.module1_widget

    @property
    def module2_widget(self):
        return self.matting_page.module2_widget

    @property
    def scroll_area(self):
        return self.matting_page.scroll_area

    def _on_prepare_transfer_clicked(self):
        self.matting_page._on_prepare_transfer_clicked()

    def _on_tab_changed(self, route_key: str):
        """
        响应选项卡点击切换：
        需求：从一个模块切换到另一个模块，原始模块与目标模块都回到初始重置状态。
        """
        if route_key == self._current_route:
            return

        # 切换大模块时，原始模块与目标模块均执行重置，恢复初始状态
        self.matting_page.reset_page()
        self.enhancer_page.reset_page()

        self._current_route = route_key

        if route_key == "matting":
            self.stacked_widget.setCurrentIndex(0)
        elif route_key == "enhancer":
            self.stacked_widget.setCurrentIndex(1)

    def _apply_theme_styling(self, is_dark: bool):
        """刷新窗口级样式、全局 Qt 调色板及下属页面与模块"""
        apply_app_palette(is_dark)
        self.setStyleSheet(get_window_qss(is_dark))

        if is_dark:
            self.app_subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.65);")
        else:
            self.app_subtitle.setStyleSheet("color: rgba(0, 0, 0, 0.60);")

        self.matting_page.update_theme(is_dark)
        self.enhancer_page.update_theme(is_dark)

    def _on_theme_changed(self, theme: Theme):
        is_dark = (theme == Theme.DARK)
        self._apply_theme_styling(is_dark)

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

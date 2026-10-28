"""
Main Application Window
Features:
- Screen-adaptive sizing (occupies ~82% of screen resolution, centered)
- Fluent Design styling & high-contrast Light/Dark theme support
- Smooth vertical scroll container: Area 1 occupies primary viewport, scroll down for Area 2
- Eye-catching '准备复制到[逻辑父文件夹]' transition button between Module 1 and Module 2
- Module 2 semi-transparent frosted lock mask with validation logic
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame
)
from qfluentwidgets import (
    SmoothScrollArea, setTheme, Theme, isDarkTheme, qconfig,
    FluentIcon, TransparentToolButton, PrimaryPushButton,
    TitleLabel, CaptionLabel, InfoBar, InfoBarPosition
)

from src.config import APP_NAME_CN, APP_NAME_EN, APP_VERSION
from src.ui.theme_helper import apply_app_palette, get_window_qss
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

        # 核心滚动视窗：右侧带有现代平滑滚动条
        self.scroll_area = SmoothScrollArea(self.central_widget)
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
        self.content_widget.setObjectName("contentWidget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 12, 16)
        self.content_layout.setSpacing(16)

        # 区域 1：模块 1（当前视区主区域）
        self.module1_widget = Module1Widget(self.content_widget)
        self.content_layout.addWidget(self.module1_widget)

        # 模块 1 与 模块 2 之间的专属衔接过渡栏（包含醒目的「准备复制到[逻辑父文件夹]」按钮）
        self.transition_bar = QFrame(self.content_widget)
        self.transition_bar.setObjectName("transitionBar")
        transition_layout = QHBoxLayout(self.transition_bar)
        transition_layout.setContentsMargins(8, 12, 8, 12)
        transition_layout.setSpacing(20)

        left_line = QFrame(self.transition_bar)
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Sunken)
        transition_layout.addWidget(left_line, stretch=1)

        # 醒目的行动按钮
        self.prepare_transfer_btn = PrimaryPushButton(
            FluentIcon.SAVE_COPY, "准备复制到[逻辑父文件夹]", self.transition_bar
        )
        self.prepare_transfer_btn.setFixedHeight(44)
        self.prepare_transfer_btn.setMinimumWidth(300)
        btn_font = self.prepare_transfer_btn.font()
        btn_font.setPointSize(11)
        btn_font.setBold(True)
        self.prepare_transfer_btn.setFont(btn_font)
        self.prepare_transfer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prepare_transfer_btn.clicked.connect(self._on_prepare_transfer_clicked)
        transition_layout.addWidget(self.prepare_transfer_btn)

        right_line = QFrame(self.transition_bar)
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Sunken)
        transition_layout.addWidget(right_line, stretch=1)

        self.content_layout.addWidget(self.transition_bar)

        # 区域 2：模块 2（初始状态被半透明遮罩覆盖）
        self.module2_widget = Module2Widget(self.content_widget)
        self.content_layout.addWidget(self.module2_widget)

        # 核心联动：模块1子文件夹变动时，右侧列表清空且模块2所有数据重置并重新半透明遮罩
        self.module1_widget.folder_list_modified.connect(self.module2_widget.reset_module)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

    def _on_prepare_transfer_clicked(self):
        """
        点击「准备复制到[逻辑父文件夹]」校验逻辑：
        1. 检查是否存在重名冲突：若列表中有指向相同目标重命名的有效待重命名图片，
           提醒“抱歉，请先解决重命名冲突。”并保持锁定。
        2. 若无冲突但列表中没有状态是“待重命名”的图片：
           提醒“抱歉，没有有效图片可以转移。”并保持锁定。
        3. 校验通过（有待重命名图片且无冲突）：
           解除模块 2 区域半透明遮罩，恢复正常显示，并平滑滚动展现。
        """
        result_table = self.module1_widget.right_result_table
        matched_items = result_table.matched_items

        # 检查重名冲突
        if len(result_table.conflicting_targets) > 0:
            conflict_names = "、".join(sorted(result_table.conflicting_targets)[:3])
            if len(result_table.conflicting_targets) > 3:
                conflict_names += f" 等 {len(result_table.conflicting_targets)} 处"

            InfoBar.warning(
                title="存在重命名冲突",
                content=f"抱歉，请先解决重命名冲突。（发现重名：{conflict_names}）",
                parent=self,
                duration=4000,
                position=InfoBarPosition.TOP
            )
            # 保持遮罩锁定
            self.module2_widget.set_locked(True)
            return

        # 严格筛选出当前处理状态为“待重命名”的图片
        pending_items = [it for it in matched_items if it.status_message == "待重命名"]

        if not pending_items:
            InfoBar.warning(
                title="无法转移",
                content="抱歉，没有有效图片可以转移。",
                parent=self,
                duration=3500,
                position=InfoBarPosition.TOP
            )
            # 保持遮罩锁定
            self.module2_widget.set_locked(True)
        else:
            # 传递有效数据项给模块2作为待分析源
            self.module2_widget.set_source_items(pending_items)

            # 解除半透明遮罩，恢复正常显示
            self.module2_widget.set_locked(False)
            InfoBar.success(
                title="已就绪",
                content=f"已成功捕获 {len(pending_items)} 张「待重命名」有效图片，模块 2 已成功解锁！",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP
            )
            # 平滑引导用户视口滚动到模块 2
            self.scroll_area.ensureWidgetVisible(self.module2_widget)

    def _apply_theme_styling(self, is_dark: bool):
        """刷新窗口级样式、全局 Qt 调色板及下属模块颜色对比度"""
        apply_app_palette(is_dark)
        self.setStyleSheet(get_window_qss(is_dark))

        if is_dark:
            self.app_subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.65);")
        else:
            self.app_subtitle.setStyleSheet("color: rgba(0, 0, 0, 0.60);")

        self.module1_widget.update_theme(is_dark)
        self.module2_widget.update_theme(is_dark)

    def _on_theme_changed(self, theme: Theme):
        is_dark = (theme == Theme.DARK)
        self._apply_theme_styling(is_dark)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        viewport_height = self.scroll_area.viewport().height()
        if viewport_height > 200:
            self.module1_widget.setMinimumHeight(max(520, viewport_height - 90))

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

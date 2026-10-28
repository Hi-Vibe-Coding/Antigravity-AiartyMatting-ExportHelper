"""
Matting Workflow Page (Tab 1)
Encapsulates Module 1, the transition button bar, and Module 2 inside a SmoothScrollArea.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from qfluentwidgets import (
    SmoothScrollArea, PrimaryPushButton, FluentIcon, InfoBar, InfoBarPosition
)

from src.ui.module1.module1_widget import Module1Widget
from src.ui.module2.module2_widget import Module2Widget


class MattingWorkflowPage(QWidget):
    """
    选项卡 1：Aiarty Image Matting（抠图）页面
    - 包含模块 1（特殊命名图片识别）
    - 衔接过渡区（准备复制到[逻辑父文件夹] 按钮）
    - 模块 2（溯源到父文件夹）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 平滑垂直滚动容器
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
        self.content_widget.setObjectName("mattingContentWidget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 12, 16)
        self.content_layout.setSpacing(16)

        # 区域 1：模块 1（特殊命名图片识别）
        self.module1_widget = Module1Widget(self.content_widget)
        self.content_layout.addWidget(self.module1_widget)

        # 模块 1 与 模块 2 之间的专属衔接过渡栏
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

        # 区域 2：模块 2（溯源到父文件夹，初始半透明遮罩锁定）
        self.module2_widget = Module2Widget(self.content_widget)
        self.content_layout.addWidget(self.module2_widget)

        # 核心联动：模块1子文件夹变动时，右侧列表清空且模块2所有数据重置并重新半透明遮罩
        self.module1_widget.folder_list_modified.connect(self.module2_widget.reset_module)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

    def _on_prepare_transfer_clicked(self):
        """
        点击「准备复制到[逻辑父文件夹]」校验逻辑：
        1. 检查是否存在重名冲突
        2. 检查是否有待重命名图片
        3. 校验通过后解锁模块2并注入数据
        """
        result_table = self.module1_widget.right_result_table
        matched_items = result_table.matched_items

        if len(result_table.conflicting_targets) > 0:
            conflict_names = "、".join(sorted(result_table.conflicting_targets)[:3])
            if len(result_table.conflicting_targets) > 3:
                conflict_names += f" 等 {len(result_table.conflicting_targets)} 处"

            InfoBar.warning(
                title="存在重命名冲突",
                content=f"抱歉，请先解决重命名冲突。（发现重名：{conflict_names}）",
                parent=self.window(),
                duration=4000,
                position=InfoBarPosition.TOP
            )
            self.module2_widget.set_locked(True)
            return

        pending_items = [it for it in matched_items if it.status_message == "待重命名"]

        if not pending_items:
            InfoBar.warning(
                title="无法转移",
                content="抱歉，没有有效图片可以转移。",
                parent=self.window(),
                duration=3500,
                position=InfoBarPosition.TOP
            )
            self.module2_widget.set_locked(True)
        else:
            self.module2_widget.set_source_items(pending_items)
            self.module2_widget.set_locked(False)
            InfoBar.success(
                title="已就绪",
                content=f"已成功捕获 {len(pending_items)} 张「待重命名」有效图片，模块 2 已成功解锁！",
                parent=self.window(),
                duration=3000,
                position=InfoBarPosition.TOP
            )
            self.scroll_area.ensureWidgetVisible(self.module2_widget)

    def reset_page(self):
        """重置抠图工作流页面（模块1与模块2均恢复初始状态，重置滚动条位置）"""
        self.module1_widget.reset_module()
        self.module2_widget.reset_module()
        self.scroll_area.verticalScrollBar().setValue(0)

    def update_theme(self, is_dark: bool):
        self.module1_widget.update_theme(is_dark)
        self.module2_widget.update_theme(is_dark)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        viewport_height = self.scroll_area.viewport().height()
        if viewport_height > 200:
            self.module1_widget.setMinimumHeight(max(520, viewport_height - 90))

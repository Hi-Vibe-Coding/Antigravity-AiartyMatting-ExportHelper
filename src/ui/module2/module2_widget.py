"""
Area 2 / Module 2 Widget with Semi-transparent Lock Mask.
Initially covered with a frosted semi-transparent mask until unlocked
by the '准备复制到[逻辑父文件夹]' action button.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedLayout
)
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, StrongBodyLabel, FluentIcon, IconWidget,
    isDarkTheme
)


class Module2Widget(CardWidget):
    """
    区域2 / 模块2 容器卡片（支持半透明锁定遮罩）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_locked = True
        self.setMinimumHeight(460)

        self._init_ui()
        self.set_locked(True)
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        self.setObjectName("module2Widget")

        # 核心层叠布局：实现半透明浮层覆盖在整个内容之上
        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # 0 层：模块 2 实际内容层
        self.content_widget = QWidget(self)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(18, 16, 18, 18)
        content_layout.setSpacing(14)

        # 区域2标题
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title = TitleLabel("模块 2：功能待接入", self.content_widget)
        self.title.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.desc = CaptionLabel("（已解锁，可正常操作本区域功能）", self.content_widget)
        header_layout.addWidget(self.desc)
        header_layout.addStretch()

        content_layout.addLayout(header_layout)

        # 占位中心展示卡片
        self.placeholder_frame = QFrame(self.content_widget)
        center_layout = QVBoxLayout(self.placeholder_frame)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(12)

        icon_widget = IconWidget(FluentIcon.TILES, self.placeholder_frame)
        icon_widget.setFixedSize(56, 56)
        center_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.tip_title = StrongBodyLabel("模块 2 区域已成功激活", self.placeholder_frame)
        self.tip_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.tip_title)

        self.tip_desc = CaptionLabel("随时提供模块2的具体业务需求，即可在此无缝嵌入相应功能界面与处理逻辑", self.placeholder_frame)
        self.tip_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.tip_desc)

        content_layout.addWidget(self.placeholder_frame, stretch=1)
        self.stacked_layout.addWidget(self.content_widget)

        # 1 层：半透明锁定遮罩层
        self.mask_overlay = QFrame(self)
        self.mask_overlay.setObjectName("module2MaskOverlay")
        mask_layout = QVBoxLayout(self.mask_overlay)
        mask_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mask_layout.setSpacing(12)

        self.mask_icon = IconWidget(FluentIcon.HIDE, self.mask_overlay)
        self.mask_icon.setFixedSize(52, 52)
        mask_layout.addWidget(self.mask_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.mask_title = StrongBodyLabel("模块 2 处于待命锁定状态", self.mask_overlay)
        self.mask_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mask_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        mask_layout.addWidget(self.mask_title)

        self.mask_desc = CaptionLabel("请先在上方核对扫描结果，并点击【准备复制到[逻辑父文件夹]】解锁此区域", self.mask_overlay)
        self.mask_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mask_layout.addWidget(self.mask_desc)

        self.stacked_layout.addWidget(self.mask_overlay)

    def set_locked(self, locked: bool):
        """控制遮罩的显示与内容的交互状态"""
        self.is_locked = locked
        self.mask_overlay.setVisible(locked)
        self.content_widget.setEnabled(not locked)
        if locked:
            self.mask_overlay.raise_()

    def update_theme(self, is_dark: bool):
        """刷新深浅主题的高对比度样式"""
        if is_dark:
            self.desc.setStyleSheet("color: rgba(255, 255, 255, 0.65); margin-top: 4px;")
            self.tip_desc.setStyleSheet("color: rgba(255, 255, 255, 0.60);")
            self.mask_desc.setStyleSheet("color: rgba(255, 255, 255, 0.65); font-size: 13px;")
            self.placeholder_frame.setStyleSheet("""
                QFrame {
                    border: 2px dashed rgba(255, 255, 255, 0.22);
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.03);
                }
            """)
            self.mask_overlay.setStyleSheet("""
                QFrame#module2MaskOverlay {
                    background-color: rgba(24, 24, 24, 0.82);
                    border: 1px dashed rgba(255, 255, 255, 0.18);
                    border-radius: 10px;
                }
            """)
        else:
            self.desc.setStyleSheet("color: rgba(0, 0, 0, 0.55); margin-top: 4px;")
            self.tip_desc.setStyleSheet("color: rgba(0, 0, 0, 0.55);")
            self.mask_desc.setStyleSheet("color: rgba(0, 0, 0, 0.60); font-size: 13px;")
            self.placeholder_frame.setStyleSheet("""
                QFrame {
                    border: 2px dashed rgba(0, 0, 0, 0.18);
                    border-radius: 8px;
                    background-color: rgba(0, 0, 0, 0.02);
                }
            """)
            self.mask_overlay.setStyleSheet("""
                QFrame#module2MaskOverlay {
                    background-color: rgba(248, 249, 250, 0.84);
                    border: 1px dashed rgba(0, 0, 0, 0.15);
                    border-radius: 10px;
                }
            """)

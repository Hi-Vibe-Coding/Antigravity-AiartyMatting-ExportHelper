"""
Area 2 / Module 2 Placeholder Widget
Reserved area for Module 2, positioned below Area 1 in the vertical scroll view.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, StrongBodyLabel, FluentIcon, IconWidget
)


class Module2Widget(CardWidget):
    """
    区域2 / 模块2 预留容器卡片
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("module2Widget")
        self.setMinimumHeight(450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        # 区域2标题
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = TitleLabel("模块 2：功能待接入")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(title)

        desc = CaptionLabel("（可通过右侧滚动条向下滑动查看）")
        desc.setStyleSheet("color: rgba(128, 128, 128, 0.85); margin-top: 4px;")
        header_layout.addWidget(desc)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 占位中心展示
        placeholder_frame = QFrame(self)
        placeholder_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed rgba(120, 120, 120, 0.25);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.02);
            }
        """)
        center_layout = QVBoxLayout(placeholder_frame)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(12)

        icon_widget = IconWidget(FluentIcon.TILES, placeholder_frame)
        icon_widget.setFixedSize(56, 56)
        center_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        tip_title = StrongBodyLabel("模块 2 区域已预留就绪")
        tip_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(tip_title)

        tip_desc = CaptionLabel("随时提供模块2的具体需求，即可在此无缝嵌入相应功能界面与处理逻辑")
        tip_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_desc.setStyleSheet("color: rgba(128, 128, 128, 0.8);")
        center_layout.addWidget(tip_desc)

        layout.addWidget(placeholder_frame, stretch=1)

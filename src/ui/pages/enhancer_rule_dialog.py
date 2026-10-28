"""
Enhancer Rule Example Dialog Panel
Visual decomposition and comparison for 'Aiarty Image Enhancer（画质增强）' filtering rules:
Pattern: [逻辑父文件夹名]__[纯数字序号].png
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy
)
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, CaptionLabel, StrongBodyLabel, BodyLabel,
    PrimaryPushButton, PushButton, FluentIcon, isDarkTheme, InfoBar, InfoBarPosition
)

ENHANCER_RULE_TEXT_SUMMARY = """【Aiarty Image Enhancer（画质增强）- 图片筛选规则解析】

文件名结构规范：[逻辑父文件夹名]__[纯数字序号].png

规则解析：
1. 扩展名必须为 .png（大小写不敏感）
2. 序号必须为纯数字组合（如 1, 0123）
3. 必须通过连续双下划线 '__' 分隔
4. 逻辑父文件夹名格式：[字母+纯数字]-[纯数字]
   - 连字符左侧：26 个英文字母在前，紧跟纯数字（如 B0, ABc00；错误如 0B, 00ABc）
   - 中间连字符：'-'
   - 连字符右侧：纯数字（如 001, 101）

典型示例对比：
• 正确：B0-001__1.png          -> 逻辑父名: B0-001, 序号: 1
• 正确：ABc00-101__0123.png     -> 逻辑父名: ABc00-101, 序号: 0123
• 正确：A1-2__3.png             -> 逻辑父名: A1-2, 序号: 3
• 错误：0B-001__1.png           (错误：数字在字母前，必须字母在前)
• 错误：00ABc-001__1.png        (错误：纯数字开头)
• 错误：B-001__1.png            (错误：字母后缺少纯数字)
• 错误：B0-ABC__1.png           (错误：连字符右侧非纯数字)
• 错误：B0-001_1.png            (错误：单下划线，缺少 __)
• 错误：B0-001__abc.png         (错误：序号非纯数字)
• 错误：B0-001__1.jpg           (错误：扩展名非 .png)
"""


class CapsuleBlock(QFrame):
    """单个字段分段彩色胶囊组件"""
    def __init__(self, main_text: str, sub_text: str, color_light: str, color_dark: str, parent=None):
        super().__init__(parent)
        self.main_text = main_text
        self.sub_text = sub_text
        self.color_light = color_light
        self.color_dark = color_dark

        self._init_ui()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self.main_label = QLabel(self.main_text, self)
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Cascadia Mono, Consolas, Courier New, monospace", 13)
        font.setBold(True)
        self.main_label.setFont(font)
        layout.addWidget(self.main_label)

        self.sub_label = QLabel(self.sub_text, self)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 11px; font-weight: 500;")
        layout.addWidget(self.sub_label)

    def update_theme(self, is_dark: bool):
        c = self.color_dark if is_dark else self.color_light
        bg = f"rgba({c}, 0.20)" if is_dark else f"rgba({c}, 0.12)"
        border = f"rgba({c}, 0.45)" if is_dark else f"rgba({c}, 0.35)"
        text_color = f"rgb({c})"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        self.main_label.setStyleSheet(f"color: {text_color}; font-weight: 700; background: transparent;")
        self.sub_label.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: 500; background: transparent;")


class EnhancerRuleExampleDialog(MessageBoxBase):
    """画质增强模块：规则示例视觉解构大面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(680)

        # 隐藏默认双按钮，使用自定义底部操作栏
        self.yesButton.hide()
        self.cancelButton.hide()

        self._init_panel_ui()

    def _init_panel_ui(self):
        root_layout = self.viewLayout
        root_layout.setContentsMargins(20, 20, 20, 16)
        root_layout.setSpacing(14)

        # 1. 顶部标题与说明
        title = SubtitleLabel("画质增强图片筛选规则解析", self)
        root_layout.addWidget(title)

        desc = CaptionLabel(
            "只有符合以下规范命名的图片才会被判定为「有效」数据，支持提取逻辑父文件夹名供后续流转：",
            self
        )
        root_layout.addWidget(desc)

        # 2. 彩色分段结构胶囊栏
        capsule_container = QWidget(self)
        capsule_layout = QHBoxLayout(capsule_container)
        capsule_layout.setContentsMargins(0, 4, 0, 4)
        capsule_layout.setSpacing(8)

        self.cap_parent = CapsuleBlock(
            "[字母+数字]-[数字]", "① 逻辑父文件夹名 (如 B0-001)",
            color_light="0, 120, 212", color_dark="96, 205, 255", parent=capsule_container
        )
        self.cap_sep = CapsuleBlock(
            "__", "② 双下划线分隔",
            color_light="107, 114, 128", color_dark="156, 163, 175", parent=capsule_container
        )
        self.cap_seq = CapsuleBlock(
            "[纯数字序号]", "③ 纯数字 (如 1, 0123)",
            color_light="234, 88, 12", color_dark="251, 146, 60", parent=capsule_container
        )
        self.cap_ext = CapsuleBlock(
            ".png", "④ 必须为 PNG 扩展名",
            color_light="16, 185, 129", color_dark="52, 211, 153", parent=capsule_container
        )

        capsule_layout.addWidget(self.cap_parent, stretch=4)
        capsule_layout.addWidget(self.cap_sep, stretch=2)
        capsule_layout.addWidget(self.cap_seq, stretch=3)
        capsule_layout.addWidget(self.cap_ext, stretch=2)
        root_layout.addWidget(capsule_container)

        # 3. 详细分解卡片 (2x2 网格)
        grid_frame = QFrame(self)
        is_dark = isDarkTheme()
        grid_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {"rgba(255, 255, 255, 0.04)" if is_dark else "rgba(0, 0, 0, 0.02)"};
                border: 1px solid {"rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.06)"};
                border-radius: 8px;
            }}
        """)
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setContentsMargins(14, 12, 14, 12)
        grid_layout.setSpacing(10)

        # 步骤 1: 扩展名
        grid_layout.addWidget(StrongBodyLabel("1. 扩展名必须为 .png", grid_frame), 0, 0)
        grid_layout.addWidget(BodyLabel("文件后缀必须为 .png (大小写不敏感，如 .png、.PNG)。", grid_frame), 0, 1)

        # 步骤 2: 纯数字序号
        grid_layout.addWidget(StrongBodyLabel("2. 必须紧接纯数字序号", grid_frame), 1, 0)
        grid_layout.addWidget(BodyLabel("双下划线右侧必须为纯数字组合（如 1、0123、101）。", grid_frame), 1, 1)

        # 步骤 3: 连续双下划线
        grid_layout.addWidget(StrongBodyLabel("3. 连续双下划线 '__'", grid_frame), 2, 0)
        grid_layout.addWidget(BodyLabel("逻辑父名与纯数字序号之间必须使用连续双下划线连接。", grid_frame), 2, 1)

        # 步骤 4: 逻辑父文件夹名
        grid_layout.addWidget(StrongBodyLabel("4. [字母+纯数字]-[纯数字]", grid_frame), 3, 0)
        grid_layout.addWidget(BodyLabel("连字符左侧为 26 个英文字母在前紧跟纯数字 (如 B0)，右侧为纯数字 (如 001)。", grid_frame), 3, 1)

        root_layout.addWidget(grid_frame)

        # 4. 正确示例 VS 错误示例对照
        example_container = QHBoxLayout()
        example_container.setSpacing(12)

        # 正确示例卡片
        good_card = QFrame(self)
        good_card.setStyleSheet(f"""
            QFrame {{
                background-color: {"rgba(16, 185, 129, 0.08)" if is_dark else "rgba(16, 185, 129, 0.06)"};
                border: 1px solid {"rgba(16, 185, 129, 0.25)" if is_dark else "rgba(16, 185, 129, 0.2)"};
                border-radius: 6px;
            }}
        """)
        good_layout = QVBoxLayout(good_card)
        good_layout.setContentsMargins(12, 10, 12, 10)
        good_layout.setSpacing(4)
        good_title = StrongBodyLabel("✔ 正确命名示例 (标记为有效)", good_card)
        good_title.setStyleSheet("color: #10b981; font-weight: 700;")
        good_layout.addWidget(good_title)
        good_layout.addWidget(CaptionLabel("• B0-001__1.png -> 父名: B0-001, 序号: 1", good_card))
        good_layout.addWidget(CaptionLabel("• ABc00-101__0123.png -> 父名: ABc00-101", good_card))
        good_layout.addWidget(CaptionLabel("• A1-2__3.png -> 父名: A1-2, 序号: 3", good_card))
        example_container.addWidget(good_card, stretch=1)

        # 错误示例卡片
        bad_card = QFrame(self)
        bad_card.setStyleSheet(f"""
            QFrame {{
                background-color: {"rgba(239, 68, 68, 0.08)" if is_dark else "rgba(239, 68, 68, 0.06)"};
                border: 1px solid {"rgba(239, 68, 68, 0.25)" if is_dark else "rgba(239, 68, 68, 0.2)"};
                border-radius: 6px;
            }}
        """)
        bad_layout = QVBoxLayout(bad_card)
        bad_layout.setContentsMargins(12, 10, 12, 10)
        bad_layout.setSpacing(4)
        bad_title = StrongBodyLabel("✘ 常见错误示例 (标记为无效)", bad_card)
        bad_title.setStyleSheet("color: #ef4444; font-weight: 700;")
        bad_layout.addWidget(bad_title)
        bad_layout.addWidget(CaptionLabel("• 0B-001__1.png (数字在字母前，必须字母在前)", bad_card))
        bad_layout.addWidget(CaptionLabel("• B-001__1.png (字母后缺少纯数字)", bad_card))
        bad_layout.addWidget(CaptionLabel("• B0-001_1.png (单下划线，缺少 '__')", bad_card))
        bad_layout.addWidget(CaptionLabel("• B0-001__1.jpg (非 .png 扩展名)", bad_card))
        example_container.addWidget(bad_card, stretch=1)

        root_layout.addLayout(example_container)

        # 5. 底部按钮操作栏
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 4, 0, 0)
        btn_bar.setSpacing(10)

        copy_btn = PushButton(FluentIcon.COPY, "复制规则说明", self)
        copy_btn.clicked.connect(self._copy_rule_text)
        btn_bar.addWidget(copy_btn)

        btn_bar.addStretch()

        close_btn = PrimaryPushButton("知道了", self)
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        btn_bar.addWidget(close_btn)

        root_layout.addLayout(btn_bar)

    def _copy_rule_text(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(ENHANCER_RULE_TEXT_SUMMARY)
        InfoBar.success(
            title="已复制",
            content="规则说明已成功复制到系统剪贴板！",
            parent=self.window(),
            duration=2000,
            position=InfoBarPosition.TOP
        )


def show_enhancer_rule_example(target_widget, parent=None):
    """弹出画质增强模块规则视觉解析弹窗"""
    dialog = EnhancerRuleExampleDialog(parent or target_widget.window())
    dialog.exec()

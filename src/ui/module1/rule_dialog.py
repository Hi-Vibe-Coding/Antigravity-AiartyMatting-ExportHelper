"""
Rule Example Dialog Panel (规则示例视觉解构大面板 - 方案 B)
Features:
- Segmented Colorful Capsule/Pill decomposition
- Right-to-Left breakdown step cards
- High-contrast visual correct / incorrect example comparisons
- Light / Dark theme responsive styling
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy
)
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, CaptionLabel, StrongBodyLabel, BodyLabel,
    PrimaryPushButton, PushButton, FluentIcon, isDarkTheme, InfoBar, InfoBarPosition
)

# 复制用的纯文本版说明
RULE_TEXT_SUMMARY = """【AiartyMatting 导出助手 - 特殊机制命名规则解析】

文件名示例：B0-001__1_attr1_subject.png

从文件名尾部（右向左）逐级分析逻辑：
1. [限定格式] 必须为 .png 扩展名（大小写不敏感）
2. [固定后缀] 必须精确全字匹配 '_attr1_subject'
3. [纯数字序号] 紧邻后缀左侧，必须为纯数字文本组合（如 1、0123、1230）
4. [双下划线] 必须存在连续 2 个下划线 '__' 分隔符
5. [逻辑父文件夹名] 位于 '__' 左侧，由连字符 '-' 分隔的两部分组成：
   - 左侧：26 个英文字母（大小写不限）拼接纯数字（如 B0, ABc00；错误如 0B, 00ABc）
   - 中间：'-' 连字符
   - 右侧：纯数字组合（如 001, 101）

推断计算结果：
- 逻辑父文件夹名：B0-001
- 目标重命名：B0-001__1.png

典型正反示例：
- 正确：B0-001__1_attr1_subject.png -> 逻辑父名: B0-001, 目标名: B0-001__1.png
- 正确：ABc00-101__0123_attr1_subject.png -> 逻辑父名: ABc00-101, 目标名: ABc00-101__0123.png
- 错误：0B-001__1_attr1_subject.png (左侧数字在字母前)
- 错误：B0-001_1_attr1_subject.png (单下划线，缺少 __)
- 错误：B0-001__1_attr1_subject.jpg (非 png 扩展名)
- 错误：B0-001__abc_attr1_subject.png (序号非纯数字)
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


class RuleExampleDialog(MessageBoxBase):
    """
    方案 B：现代卡片 / 胶囊分段视觉解构大面板
    永不错位，清晰美观
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setClosableOnMaskClicked(True)

        parent_w = parent.width() if parent else 1200
        target_w = max(980, min(1040, int(parent_w * 0.90)))
        self.widget.setMinimumWidth(target_w)

        self.capsules = []
        self._init_ui()
        self._apply_theme_styling(isDarkTheme())

    def _init_ui(self):
        # 头部标题
        self.titleLabel = SubtitleLabel("特殊机制命名规则解析与视觉解构", self)
        self.titleLabel.setStyleSheet("font-size: 19px; font-weight: 700;")
        self.viewLayout.addWidget(self.titleLabel)

        header_desc = CaptionLabel("系统将严格从文件名尾部（右向左）进行逆向层级分析与逻辑名推导：", self)
        header_desc.setStyleSheet("margin-bottom: 8px;")
        self.viewLayout.addWidget(header_desc)

        # 1. 顶部彩色胶囊分解容器
        self.ribbon_card = QFrame(self)
        ribbon_layout = QVBoxLayout(self.ribbon_card)
        ribbon_layout.setContentsMargins(14, 12, 14, 14)
        ribbon_layout.setSpacing(10)

        # 逆向解析方向箭头提示
        direction_label = CaptionLabel("◀──  逆向分析流向：从尾部格式依次向左校验与提取  ◀──", self.ribbon_card)
        direction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        direction_label.setStyleSheet("color: #0078d4; font-weight: 600; font-size: 12px;")
        ribbon_layout.addWidget(direction_label)

        # 胶囊水平横条
        capsules_layout = QHBoxLayout()
        capsules_layout.setSpacing(8)

        # ① 逻辑父文件夹名 (蓝色)
        c_parent = CapsuleBlock("B0-001", "① 逻辑父文件夹名", "0, 120, 212", "96, 205, 255", self.ribbon_card)
        # ② 双下划线 (灰色)
        c_sep = CapsuleBlock("__", "② 双下划线分隔", "100, 116, 139", "148, 163, 184", self.ribbon_card)
        # ③ 纯数字序号 (紫色)
        c_seq = CapsuleBlock("1", "③ 纯数字序号", "126, 34, 206", "192, 132, 252", self.ribbon_card)
        # ④ 特殊机制后缀 (琥珀橙)
        c_suffix = CapsuleBlock("_attr1_subject", "④ 特殊机制固定后缀", "217, 119, 6", "251, 191, 36", self.ribbon_card)
        # ⑤ 扩展名 (翡翠绿)
        c_ext = CapsuleBlock(".png", "⑤ 限定格式", "5, 150, 105", "52, 211, 153", self.ribbon_card)

        self.capsules.extend([c_parent, c_sep, c_seq, c_suffix, c_ext])

        capsules_layout.addWidget(c_parent, stretch=3)
        capsules_layout.addWidget(c_sep, stretch=1)
        capsules_layout.addWidget(c_seq, stretch=1)
        capsules_layout.addWidget(c_suffix, stretch=3)
        capsules_layout.addWidget(c_ext, stretch=2)

        ribbon_layout.addLayout(capsules_layout)

        # 计算结果横幅
        result_bar = QHBoxLayout()
        result_bar.setSpacing(24)
        result_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.res_parent_lbl = StrongBodyLabel("推导逻辑父文件夹名：B0-001", self.ribbon_card)
        self.res_rename_lbl = StrongBodyLabel("目标重命名文件：B0-001__1.png", self.ribbon_card)
        result_bar.addWidget(self.res_parent_lbl)
        result_bar.addWidget(self.res_rename_lbl)
        ribbon_layout.addLayout(result_bar)

        self.viewLayout.addWidget(self.ribbon_card)

        # 2. 中部：四步详细规则卡片 (2x2 网格)
        self.steps_card = QFrame(self)
        steps_layout = QGridLayout(self.steps_card)
        steps_layout.setContentsMargins(14, 12, 14, 12)
        steps_layout.setHorizontalSpacing(16)
        steps_layout.setVerticalSpacing(10)

        # Step 1
        steps_layout.addWidget(self._create_step_widget(
            "步骤 1 [尾部扩展名]",
            "必须为 .png 格式（大小写不敏感，.png / .PNG 均可识别）。",
            "5, 150, 105", "52, 211, 153"
        ), 0, 0)

        # Step 2
        steps_layout.addWidget(self._create_step_widget(
            "步骤 2 [固定后缀校验]",
            "扩展名前必须完全匹配特殊后缀 '_attr1_subject'，少字错字均视为无效。",
            "217, 119, 6", "251, 191, 36"
        ), 0, 1)

        # Step 3
        steps_layout.addWidget(self._create_step_widget(
            "步骤 3 [纯数字序号提取]",
            "后缀左侧必须为纯数字字符组合（0~9，如 1、0123、1230），不可掺杂字母或符号。",
            "126, 34, 206", "192, 132, 252"
        ), 1, 0)

        # Step 4
        steps_layout.addWidget(self._create_step_widget(
            "步骤 4 [双下划线与逻辑父名]",
            "必须包含连续 2 个 '_' 分隔；剩余部分为 [字母+纯数字]-[纯数字]（如 B0-001、ABc00-101）。",
            "0, 120, 212", "96, 205, 255"
        ), 1, 1)

        self.viewLayout.addWidget(self.steps_card)

        # 3. 底部：典型正反示例对比
        self.examples_card = QFrame(self)
        examples_layout = QHBoxLayout(self.examples_card)
        examples_layout.setContentsMargins(14, 10, 14, 10)
        examples_layout.setSpacing(16)

        # 正确示例列
        valid_col = QVBoxLayout()
        valid_col.setSpacing(4)
        v_title = StrongBodyLabel("✔ 正确有效示例", self.examples_card)
        v_title.setStyleSheet("color: #107c10; font-weight: 600;")
        valid_col.addWidget(v_title)

        v1 = CaptionLabel("• B0-001__1_attr1_subject.png  ➔ 逻辑父名: B0-001 | 重命名: B0-001__1.png", self.examples_card)
        v2 = CaptionLabel("• ABc00-101__0123_attr1_subject.png  ➔ 逻辑父名: ABc00-101 | 重命名: ABc00-101__0123.png", self.examples_card)
        valid_col.addWidget(v1)
        valid_col.addWidget(v2)
        examples_layout.addLayout(valid_col, stretch=1)

        # 错误示例列
        invalid_col = QVBoxLayout()
        invalid_col.setSpacing(4)
        iv_title = StrongBodyLabel("✖ 典型错误示例", self.examples_card)
        iv_title.setStyleSheet("color: #d13438; font-weight: 600;")
        invalid_col.addWidget(iv_title)

        iv1 = CaptionLabel("• 0B-001__1_attr1_subject.png (左侧数字在字母前，非法)", self.examples_card)
        iv2 = CaptionLabel("• B0-001_1_attr1_subject.png (单下划线，缺少连续 __ 分隔)", self.examples_card)
        iv3 = CaptionLabel("• B0-001__1_attr1_subject.jpg (格式非 .png，不被采纳)", self.examples_card)
        invalid_col.addWidget(iv1)
        invalid_col.addWidget(iv2)
        invalid_col.addWidget(iv3)
        examples_layout.addLayout(invalid_col, stretch=1)

        self.viewLayout.addWidget(self.examples_card)

        # 4. 底部按钮配置
        self.copy_btn = PushButton(FluentIcon.COPY, "复制规则文本", self.buttonGroup)
        self.copy_btn.setFixedHeight(34)
        self.copy_btn.clicked.connect(self._copy_text)
        self.buttonLayout.insertWidget(0, self.copy_btn)

        self.cancelButton.hide()
        self.yesButton.setText("我知道了")
        self.yesButton.setFixedHeight(34)

    def _create_step_widget(self, step_title: str, step_desc: str, c_light: str, c_dark: str) -> QWidget:
        w = QFrame(self.steps_card)
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(3)

        title = StrongBodyLabel(step_title, w)
        title.setStyleSheet(f"font-size: 13px; font-weight: 600;")
        l.addWidget(title)

        desc = CaptionLabel(step_desc, w)
        desc.setWordWrap(True)
        desc.setStyleSheet("line-height: 1.4;")
        l.addWidget(desc)

        w.setProperty("step_frame", True)
        return w

    def _apply_theme_styling(self, is_dark: bool):
        # 容器背景卡片样式
        card_bg = "rgba(255, 255, 255, 0.04)" if is_dark else "rgba(0, 0, 0, 0.02)"
        card_border = "rgba(255, 255, 255, 0.10)" if is_dark else "rgba(0, 0, 0, 0.08)"

        sub_card_style = f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
            }}
            QFrame[step_frame="true"] {{
                background-color: {'rgba(255, 255, 255, 0.03)' if is_dark else 'rgba(255, 255, 255, 0.65)'};
                border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
                border-radius: 6px;
            }}
        """

        self.ribbon_card.setStyleSheet(sub_card_style)
        self.steps_card.setStyleSheet(sub_card_style)
        self.examples_card.setStyleSheet(sub_card_style)

        # 结果标签着色
        self.res_parent_lbl.setStyleSheet(f"color: {'#60cdff' if is_dark else '#0078d4'}; font-weight: 600; font-size: 13px;")
        self.res_rename_lbl.setStyleSheet(f"color: {'#52c41a' if is_dark else '#237804'}; font-weight: 600; font-size: 13px;")

        # 同步胶囊组件主题
        for c in self.capsules:
            c.update_theme(is_dark)

    def _copy_text(self):
        QGuiApplication.clipboard().setText(RULE_TEXT_SUMMARY)
        top_window = self.window()
        InfoBar.success(
            title="复制成功",
            content="规则解析说明与对照示例已成功复制到系统剪贴板！",
            parent=top_window,
            duration=2000,
            position=InfoBarPosition.TOP
        )


def show_rule_example_panel(target_btn: QWidget, parent_window: QWidget = None):
    """弹出方案 B 现代化视觉解构大面板"""
    parent = parent_window or target_btn.window()
    dialog = RuleExampleDialog(parent)
    dialog.exec()

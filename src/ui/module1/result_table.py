"""
Result Table & Action Area (Module 1 Right Box)
Displays ALL image files in the scanned folders, clearly distinguishing between:
- "待重命名" (Valid pattern match: B0-001__1_attr1_subject.png)
- "无效" (Invalid format or pattern: cannot be processed)
Supports:
- "只显示有效" filter checkbox (default unchecked)
- Automatic conflict detection: graying out "一键应用重命名" when duplicate target names exist
- Target conflict cells highlighted in vivid bold RED
- Bottom warning status line animated as an infinite scrolling marquee (从右往左跑马灯循环滚动)
"""
from collections import Counter
from pathlib import Path
from typing import List, Set

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QBrush, QFont, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QHeaderView, QTableWidgetItem, QSizePolicy
)
from qfluentwidgets import (
    TableWidget, PrimaryPushButton, PushButton, IndeterminateProgressBar,
    FluentIcon, SubtitleLabel, CaptionLabel, CheckBox, InfoBar, InfoBarPosition,
    isDarkTheme
)

from src.config import MatchedImageItem


class MarqueeStatusLabel(QWidget):
    """
    状态栏警示跑马灯组件：
    - 支持静态文本模式与动态从右向左无缝循环滚动跑马灯模式
    - 鼠标悬停时自动暂停，移开自动恢复
    - 适配深色 / 浅色模式高对比度大红色
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._is_marquee = False
        self._offset = 0.0
        self._gap = 70
        self._color = QColor("#e81123")
        self._is_paused = False

        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 40 fps 平滑定时器
        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._on_tick)

        font = QFont("Segoe UI", 10)
        font.setBold(True)
        self.setFont(font)

    def is_marquee(self) -> bool:
        return self._is_marquee

    def text(self) -> str:
        return self._text

    def clear(self):
        self.setText("", is_marquee=False)

    def setText(self, text: str, is_marquee: bool = False, color: QColor = None):
        self._text = text
        self._is_marquee = is_marquee
        if color:
            self._color = color

        if is_marquee and text:
            # 初始从控件可视右侧边缘进入
            self._offset = float(self.width() if self.width() > 50 else 350)
            self._is_paused = False
            self._timer.start()
        else:
            self._timer.stop()
            self._offset = 0.0

        self.update()

    def setColor(self, color: QColor):
        self._color = color
        self.update()

    def enterEvent(self, event):
        if self._is_marquee:
            self._is_paused = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._is_marquee:
            self._is_paused = False
        super().leaveEvent(event)

    def _on_tick(self):
        if not self._is_marquee or not self._text or self._is_paused:
            return

        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._text)
        cycle = text_w + self._gap

        # 平滑向左移动
        self._offset -= 1.6
        if self._offset <= -cycle:
            self._offset += cycle

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._color)
        painter.setFont(self.font())

        fm = self.fontMetrics()
        y = (self.height() + fm.ascent() - fm.descent()) // 2

        if not self._text:
            return

        # 静态显示模式
        if not self._is_marquee:
            painter.drawText(0, y, self._text)
            return

        # 动态跑马灯无缝循环显示模式（从右往左）
        text_w = fm.horizontalAdvance(self._text)
        cycle = text_w + self._gap

        x = self._offset
        # 连续绘制直到填满视窗宽度
        while x < self.width():
            if x + text_w > 0:
                painter.drawText(int(x), y, self._text)
            x += cycle


class ResultTableWidget(QFrame):
    """
    模块1右侧结果区：表格呈现与批量操作
    """
    rename_requested = Signal(list)  # List[MatchedImageItem]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.matched_items: List[MatchedImageItem] = []
        self.conflicting_targets: Set[str] = set()

        self._init_ui()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        self.setObjectName("resultTableFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 头部标题、统计信息与筛选控制
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title_label = SubtitleLabel("图片列表", self)
        header_layout.addWidget(self.title_label)

        self.count_label = CaptionLabel("(0 项)", self)
        header_layout.addWidget(self.count_label)

        # “只显示有效”复选框（默认不勾选）
        self.only_valid_checkbox = CheckBox("只显示有效", self)
        self.only_valid_checkbox.setChecked(False)
        self.only_valid_checkbox.setToolTip("勾选后仅展示处理状态为「待重命名」的数据")
        self.only_valid_checkbox.stateChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.only_valid_checkbox)

        header_layout.addStretch()

        # 精简高质感的规则说明胶囊
        self.rule_tag = CaptionLabel("规则: [逻辑父名]__[序号]_attr1_subject.png", self)
        header_layout.addWidget(self.rule_tag)

        # 规则示例按钮
        self.rule_example_btn = PushButton(FluentIcon.INFO, "规则示例", self)
        self.rule_example_btn.setFixedHeight(30)
        self.rule_example_btn.clicked.connect(self._show_rule_example)
        header_layout.addWidget(self.rule_example_btn)

        layout.addLayout(header_layout)

        # 进度指示器（扫描时显示）
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 结果表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        headers = [
            "序号", "所在子文件夹", "原文件名", "逻辑父文件夹名", "目标重命名", "处理状态"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectRightClickedRow(True)

        # 设置表头对齐方式（与单元格保持 100% 垂直咬合）
        self.table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(2).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(3).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeaderItem(4).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(5).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 列宽分配模式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)          # 序号
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)    # 所在子文件夹
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)        # 原文件名
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)    # 逻辑父文件夹名
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)        # 目标重命名
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)          # 处理状态

        self.table.setColumnWidth(0, 52)   # 序号
        self.table.setColumnWidth(1, 190)  # 所在子文件夹（动态自适应并保底 190px）
        self.table.setColumnWidth(3, 140)  # 逻辑父文件夹名
        self.table.setColumnWidth(5, 100)  # 处理状态

        layout.addWidget(self.table, stretch=1)

        # 空状态占位提示
        self.empty_label = QLabel(
            "暂无扫描结果\n请在左侧拖入子文件夹并点击【开始扫描】\n将自动列出所有图片并标记「待重命名」或「无效」",
            self
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        # 底部操作栏：左侧跑马灯状态提示行，右侧操作按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        # 状态栏警示提示行（支持跑马灯流动警示）
        self.status_info = MarqueeStatusLabel(self)
        bottom_layout.addWidget(self.status_info, stretch=1)

        self.clear_table_btn = PushButton(FluentIcon.DELETE, "清空结果", self)
        self.clear_table_btn.setFixedHeight(34)
        self.clear_table_btn.clicked.connect(self.clear_results)
        bottom_layout.addWidget(self.clear_table_btn)

        self.rename_btn = PrimaryPushButton(FluentIcon.EDIT, "一键应用重命名", self)
        self.rename_btn.setFixedHeight(34)
        self.rename_btn.clicked.connect(self._on_rename_clicked)
        self.rename_btn.hide()  # 需求：隐藏一键应用重命名按钮
        bottom_layout.addWidget(self.rename_btn)

        layout.addLayout(bottom_layout)

        self._update_view()

    def _get_displayed_items(self) -> List[MatchedImageItem]:
        """获取当前列表应展示的数据项（受“只显示有效”复选框影响）"""
        if self.only_valid_checkbox.isChecked():
            return [it for it in self.matched_items if it.status_message == "待重命名"]
        return self.matched_items

    def _on_filter_changed(self):
        """当“只显示有效”勾选状态改变时，刷新表格视图"""
        self._refresh_table_rows()

    def update_theme(self, is_dark: bool):
        """刷新深浅主题的高对比度样式"""
        if is_dark:
            self.count_label.setStyleSheet("color: rgba(255, 255, 255, 0.65); font-weight: 500;")
            self.rule_tag.setStyleSheet("""
                background-color: rgba(0, 120, 212, 0.20);
                color: #60cdff;
                padding: 4px 10px;
                border-radius: 4px;
                border: 1px solid rgba(0, 120, 212, 0.35);
                font-weight: 500;
            """)
            self.empty_label.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-size: 14px; line-height: 1.6;")
            self.table.setStyleSheet("""
                QTableView {
                    background-color: transparent;
                    color: #ffffff;
                    gridline-color: rgba(255, 255, 255, 0.08);
                }
                QTableView::item {
                    padding: 4px 8px;
                }
                QHeaderView::section {
                    color: rgba(255, 255, 255, 0.85);
                    background-color: rgba(255, 255, 255, 0.04);
                    font-weight: 600;
                    padding-left: 8px;
                    padding-right: 8px;
                }
            """)
        else:
            self.count_label.setStyleSheet("color: rgba(0, 0, 0, 0.60); font-weight: 500;")
            self.rule_tag.setStyleSheet("""
                background-color: rgba(0, 120, 212, 0.08);
                color: #0078d4;
                padding: 4px 10px;
                border-radius: 4px;
                border: 1px solid rgba(0, 120, 212, 0.20);
                font-weight: 500;
            """)
            self.empty_label.setStyleSheet("color: rgba(0, 0, 0, 0.50); font-size: 14px; line-height: 1.6;")
            self.table.setStyleSheet("""
                QTableView {
                    background-color: transparent;
                    color: #1a1a1a;
                    gridline-color: rgba(0, 0, 0, 0.06);
                }
                QTableView::item {
                    padding: 4px 8px;
                }
                QHeaderView::section {
                    color: rgba(0, 0, 0, 0.75);
                    background-color: rgba(0, 0, 0, 0.02);
                    font-weight: 600;
                    padding-left: 8px;
                    padding-right: 8px;
                }
            """)

        self._refresh_table_rows()

    def set_loading(self, loading: bool):
        if loading:
            self.progress_bar.show()
            self.progress_bar.start()
            self.rename_btn.setEnabled(False)
        else:
            self.progress_bar.stop()
            self.progress_bar.hide()
            self._update_view()

    def set_results(self, items: List[MatchedImageItem]):
        self.matched_items = items
        self._refresh_table_rows()

    def _refresh_table_rows(self):
        """刷新渲染表格的所有行数据、冲突检测与大红色高亮"""
        self.table.setRowCount(0)
        is_dark = isDarkTheme()

        # 检测目标重命名重名冲突：找出不止 1 条数据指向相同目标名称的情况
        valid_targets = [it.target_name for it in self.matched_items if it.is_valid and it.target_name != "-"]
        target_counts = Counter(valid_targets)
        self.conflicting_targets = {name for name, count in target_counts.items() if count > 1}

        # 调色板：醒目大红色（深浅自适应高对比度）
        vivid_red = QColor("#ff4d4f" if is_dark else "#e81123")
        text_color = QColor("#ffffff" if is_dark else "#1a1a1a")
        black_color = QColor("#ffffff" if is_dark else "#000000")  # 无冲突加粗黑色（暗黑模式适配反白清晰呈现）
        muted_color = QColor("#8c8c8c" if is_dark else "#8c8c8c")
        accent_blue = QColor("#60cdff" if is_dark else "#0078d4")
        success_green = QColor("#52c41a" if is_dark else "#237804")

        mono_font = QFont("Cascadia Mono, Consolas, Courier New, monospace")

        displayed_items = self._get_displayed_items()

        for row, item in enumerate(displayed_items):
            self.table.insertRow(row)
            is_conflict = (item.target_name in self.conflicting_targets)

            # 0. 序号 (居中)
            item_idx = QTableWidgetItem(str(row + 1))
            item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_idx.setForeground(QBrush(text_color if item.is_valid else muted_color))
            self.table.setItem(row, 0, item_idx)

            # 1. 所在子文件夹 (左对齐，完整显示向上计算的相对目录)
            display_folder = item.folder_display_name if item.folder_display_name else item.folder_path.name
            item_folder = QTableWidgetItem(display_folder)
            item_folder.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_folder.setForeground(QBrush(text_color if item.is_valid else muted_color))
            item_folder.setToolTip(f"完整物理路径：\n{item.folder_path}")
            self.table.setItem(row, 1, item_folder)

            # 2. 原文件名 (左对齐)
            item_orig = QTableWidgetItem(item.original_name)
            item_orig.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_orig.setForeground(QBrush(text_color if item.is_valid else muted_color))
            if not item.is_valid:
                item_orig.setToolTip(f"该图片无法处理：{item.invalid_reason}")
            self.table.setItem(row, 2, item_orig)

            # 3. 提取的逻辑父文件夹名称 (居中)
            item_logic = QTableWidgetItem(item.logical_parent)
            item_logic.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if item.is_valid:
                item_logic.setForeground(QBrush(accent_blue))
                f = item_logic.font()
                f.setBold(True)
                item_logic.setFont(f)
            else:
                item_logic.setForeground(QBrush(muted_color))
            self.table.setItem(row, 3, item_logic)

            # 4. 目标重命名：
            # - 有重名冲突：大红色加粗
            # - 无重名冲突且有效：加粗黑色
            # - 无效数据：置灰
            item_target = QTableWidgetItem(item.target_name)
            item_target.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if is_conflict:
                item_target.setForeground(QBrush(vivid_red))  # 大红色
                f = item_target.font()
                f.setBold(True)
                item_target.setFont(f)
                item_target.setToolTip(f"[重名冲突警告] 列表中存在不止 1 条数据指向该目标文件名：{item.target_name}！")
            elif item.is_valid:
                item_target.setForeground(QBrush(black_color))  # 加粗黑色（浅色模式纯黑，深色模式高亮纯白）
                f = item_target.font()
                f.setBold(True)
                item_target.setFont(f)
            else:
                item_target.setForeground(QBrush(muted_color))
            self.table.setItem(row, 4, item_target)

            # 5. 处理状态 (居中)：
            # - 有重名冲突：大红色且文字为「待重命名 !」(或带感叹号)
            # - 无重名冲突且有效：
            #     已更名 -> 绿色
            #     待重命名 -> 强调蓝
            # - 无效数据：大红色
            status_text = item.status_message
            if is_conflict and item.is_valid and not item.is_renamed:
                status_text = "待重命名 !"

            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if is_conflict and item.is_valid and not item.is_renamed:
                item_status.setForeground(QBrush(vivid_red))  # 冲突时：处理状态也是大红色
                f = item_status.font()
                f.setBold(True)
                item_status.setFont(f)
                item_status.setToolTip(f"该项存在重名冲突，目标名「{item.target_name}」被重复引用！")
            elif item.is_valid:
                if item.is_renamed:
                    item_status.setForeground(QBrush(success_green))
                else:
                    item_status.setForeground(QBrush(accent_blue))
                    f = item_status.font()
                    f.setBold(True)
                    item_status.setFont(f)
            else:
                item_status.setForeground(QBrush(vivid_red))
                item_status.setToolTip(f"原因：{item.invalid_reason}")

            self.table.setItem(row, 5, item_status)

        self._adjust_column_widths()
        self._update_view()

    def _adjust_column_widths(self):
        """根据实际内容动态拓宽第 1 列（所在子文件夹），确保至少 190px 且不遮挡内容"""
        self.table.resizeColumnToContents(1)
        w1 = max(190, self.table.columnWidth(1) + 24)
        self.table.setColumnWidth(1, w1)

    def update_rename_progress(self, current: int, total: int, filename: str):
        is_dark = isDarkTheme()
        c = QColor("#60cdff" if is_dark else "#0078d4")
        self.status_info.setText(f"正在重命名有效图片 ({current}/{total}): {filename}", is_marquee=False, color=c)

    def update_rename_results(self, success_count: int, fail_count: int, items: List[MatchedImageItem]):
        self.set_results(items)
        is_dark = isDarkTheme()
        c = QColor("#52c41a" if is_dark else "#237804")
        self.status_info.setText(
            f"重命名完成：成功更名 {success_count} 个有效文件，失败/冲突 {fail_count} 个",
            is_marquee=False,
            color=c
        )

    def clear_results(self):
        self.matched_items.clear()
        self.conflicting_targets.clear()
        self.table.setRowCount(0)
        self.status_info.clear()
        self._update_view()

    def _update_view(self):
        total_count = len(self.matched_items)
        valid_count = sum(1 for it in self.matched_items if it.is_valid)
        invalid_count = total_count - valid_count
        displayed_count = len(self._get_displayed_items())

        # 统计文本提示
        if total_count > 0:
            if self.only_valid_checkbox.isChecked():
                self.count_label.setText(f"(已筛选: {displayed_count} 项 · 总计: {total_count} 项)")
            else:
                self.count_label.setText(f"(共 {total_count} 项 · 有效: {valid_count} · 无效: {invalid_count})")
        else:
            self.count_label.setText("(0 项)")

        has_items = displayed_count > 0
        self.table.setVisible(has_items)
        self.empty_label.setVisible(not has_items)
        self.clear_table_btn.setEnabled(total_count > 0)

        # 核心需求：重名冲突检测、按钮变灰与大红色跑马灯循环滚动警示
        has_conflict = len(self.conflicting_targets) > 0
        unprocessed_valid = sum(1 for it in self.matched_items if it.is_valid and not it.is_renamed)
        is_dark = isDarkTheme()
        vivid_red = QColor("#ff4d4f" if is_dark else "#e81123")

        if has_conflict:
            self.rename_btn.setEnabled(False)  # 按钮变灰不可点击
            conflict_names = "、".join(sorted(self.conflicting_targets)[:3])
            if len(self.conflicting_targets) > 3:
                conflict_names += f" 等 {len(self.conflicting_targets)} 处"

            self.rename_btn.setText("存在重名冲突 (已禁用)")
            self.rename_btn.setToolTip(f"检测到存在重名冲突：{conflict_names}，禁止执行一键重命名！")

            # 状态栏大红色跑马灯：从右向左自动无缝循环移动
            warning_msg = f"⚠️ 警告：检测到列表中有多条数据指向相同的目标重命名（{conflict_names}），一键重命名已锁定！"
            self.status_info.setText(warning_msg, is_marquee=True, color=vivid_red)
        else:
            self.rename_btn.setToolTip("")
            self.rename_btn.setEnabled(unprocessed_valid > 0)
            if unprocessed_valid > 0:
                self.rename_btn.setText(f"一键应用重命名 ({unprocessed_valid})")
            else:
                self.rename_btn.setText("一键应用重命名")

            # 若先前是跑马灯且冲突已解除，恢复静态提示
            if self.status_info.is_marquee():
                normal_c = QColor("#ffffff" if is_dark else "#1a1a1a")
                self.status_info.setText("", is_marquee=False, color=normal_c)

    def _on_rename_clicked(self):
        if len(self.conflicting_targets) > 0:
            InfoBar.error(
                title="存在重名冲突",
                content="检测到列表中有多条图片指向相同的目标重命名，无法执行重命名！",
                parent=self.window(),
                duration=3500,
                position=InfoBarPosition.TOP
            )
            return

        valid_targets = [it for it in self.matched_items if it.is_valid and not it.is_renamed]
        if not valid_targets:
            InfoBar.warning(
                title="无待处理项",
                content="列表中没有符合规则的有效待重命名图片。",
                parent=self.window(),
                duration=2500,
                position=InfoBarPosition.TOP
            )
            return
        self.rename_requested.emit(self.matched_items)

    def _show_rule_example(self):
        from src.ui.module1.rule_dialog import show_rule_example_panel
        show_rule_example_panel(self.rule_example_btn, self.window())

"""
Exclusive Data Table Widget (Module 2 Right Box)
Displays analysis results matching Module 1 items against Module 2's source folder.
Shows status: '已匹配' vs '无法找到' with high-contrast colors and tooltips.
"""
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QTableWidgetItem
)
from qfluentwidgets import (
    TableWidget, SubtitleLabel, CaptionLabel, PushButton, FluentIcon,
    isDarkTheme, IndeterminateProgressBar
)

from src.core.tracer import LogicalTraceItem


class TraceResultTableWidget(QWidget):
    """
    模块2右侧：对照数据表
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trace_items: List[LogicalTraceItem] = []

        self._init_ui()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 头部标题与统计
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title = SubtitleLabel("对照数据表", self)
        self.title.setStyleSheet("font-size: 15px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.count_label = CaptionLabel("(0 项)", self)
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        self.rule_tip = CaptionLabel("状态匹配: 在目标源文件夹下查找同名逻辑父文件夹", self)
        header_layout.addWidget(self.rule_tip)

        layout.addLayout(header_layout)

        # 进度指示器
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 对照数据表格（4列：序号、原文件、预期重命名、状态）
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        headers = [
            "序号", "原文件", "预期重命名", "状态"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectRightClickedRow(True)

        # 对齐方式
        self.table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(2).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(3).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 列宽模式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)          # 序号
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)        # 原文件
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)    # 预期重命名
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)        # 状态

        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(2, 170)

        layout.addWidget(self.table, stretch=1)

        # 空状态提示
        self.empty_label = QLabel(
            "暂无分析数据\n请在左侧拖入「源文件夹」并点击【开始分析】\n系统将自动校验每个逻辑父文件夹并计算写入目标",
            self
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        # 底部状态栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.status_label = CaptionLabel("等待分析指令...", self)
        bottom_layout.addWidget(self.status_label, stretch=1)

        self.clear_btn = PushButton(FluentIcon.DELETE, "清空列表", self)
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setEnabled(False)
        bottom_layout.addWidget(self.clear_btn)

        layout.addLayout(bottom_layout)

        self._update_view()

    def set_results(self, items: List[LogicalTraceItem]):
        self.trace_items = items
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(0)
        is_dark = isDarkTheme()

        # 调色板定义
        text_color = QColor("#ffffff" if is_dark else "#1a1a1a")
        accent_blue = QColor("#60cdff" if is_dark else "#0078d4")
        success_green = QColor("#52c41a" if is_dark else "#237804")
        warning_orange = QColor("#fa8c16" if is_dark else "#d46b08")  # 警示橙色（覆盖警告/同名不唯一）
        vivid_red = QColor("#ff4d4f" if is_dark else "#e81123")       # 错误大红色
        muted_color = QColor("#8c8c8c" if is_dark else "#8c8c8c")

        for row, item in enumerate(self.trace_items):
            self.table.insertRow(row)

            # 0. 序号 (居中)
            item_idx = QTableWidgetItem(str(row + 1))
            item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_idx.setForeground(QBrush(text_color))
            self.table.setItem(row, 0, item_idx)

            # 1. 原文件 (左对齐，尽可能显示2层文件夹及文件名)
            item_orig = QTableWidgetItem(item.raw_file_display)
            item_orig.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_orig.setForeground(QBrush(text_color))
            if item.full_source_file:
                item_orig.setToolTip(f"原文件完整物理路径：\n{item.full_source_file}")
            self.table.setItem(row, 1, item_orig)

            # 2. 预期重命名 (左对齐，加粗黑色/白色)
            item_expected = QTableWidgetItem(item.expected_rename)
            item_expected.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_expected.setForeground(QBrush(text_color))
            f = item_expected.font()
            f.setBold(True)
            item_expected.setFont(f)
            self.table.setItem(row, 2, item_expected)

            # 3. 状态 (标准原生文本呈现，不使用内部独立着色)
            status_item = QTableWidgetItem(item.status_display)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            f_status = status_item.font()
            f_status.setBold(True)
            status_item.setFont(f_status)

            if item.status_type == "normal":
                # 即将被写入到[XXXX]
                status_item.setForeground(QBrush(success_green))
                if item.dest_file_path:
                    status_item.setToolTip(f"目标完整路径：\n{item.dest_file_path}")
            elif item.status_type == "override":
                # 即将被写入到[XXXX](同名文件将覆盖!)
                status_item.setForeground(QBrush(warning_orange))
                if item.dest_file_path:
                    status_item.setToolTip(f"[注意] 该目标路径下已存在同名图片文件，继续操作将被覆盖：\n{item.dest_file_path}")
            elif item.status_display == "同名文件夹不唯一":
                status_item.setForeground(QBrush(warning_orange))
                cand_str = "\n".join(str(p) for p in (item.candidate_folders or []))
                status_item.setToolTip(f"[冲突] 源文件夹下存在多个名为「{item.logical_parent}」的子文件夹：\n{cand_str}")
            else:
                # 无法找到
                status_item.setForeground(QBrush(vivid_red))
                status_item.setToolTip(f"在源文件夹中未找到名为「{item.logical_parent}」的文件夹！")

            self.table.setItem(row, 3, status_item)

        self._update_view()

    def clear_results(self):
        self.trace_items.clear()
        self.table.setRowCount(0)
        self.status_label.setText("列表已清空")
        self._update_view()

    def _update_view(self):
        total = len(self.trace_items)
        normal_count = sum(1 for it in self.trace_items if it.status_type == "normal")
        override_count = sum(1 for it in self.trace_items if it.status_type == "override")
        ambiguous_count = sum(1 for it in self.trace_items if it.status_display == "同名文件夹不唯一")
        not_found_count = sum(1 for it in self.trace_items if it.status_display == "无法找到")

        if total > 0:
            count_parts = [f"即将写入: {normal_count}"]
            if override_count > 0:
                count_parts.append(f"将覆盖: {override_count}")
            if ambiguous_count > 0:
                count_parts.append(f"同名不唯一: {ambiguous_count}")
            if not_found_count > 0:
                count_parts.append(f"无法找到: {not_found_count}")

            self.count_label.setText(f"(共 {total} 项 · " + " · ".join(count_parts) + ")")
            self.status_label.setText(
                f"分析完成：共检索 {total} 条数据，{normal_count} 项即将写入，{override_count} 项将覆盖，{ambiguous_count} 项同名不唯一，{not_found_count} 项无法找到"
            )
        else:
            self.count_label.setText("(0 项)")

        has_items = total > 0
        self.table.setVisible(has_items)
        self.empty_label.setVisible(not has_items)
        self.clear_btn.setEnabled(has_items)

    def update_theme(self, is_dark: bool):
        if is_dark:
            self.count_label.setStyleSheet("color: rgba(255, 255, 255, 0.65); font-weight: 500;")
            self.rule_tip.setStyleSheet("color: rgba(255, 255, 255, 0.60);")
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
            self.rule_tip.setStyleSheet("color: rgba(0, 0, 0, 0.55);")
            self.empty_label.setStyleSheet("color: rgba(0, 0, 0, 0.45); font-size: 14px; line-height: 1.6;")
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
        self._refresh_table()

"""
Enhancer Module 1 Result Table (Right Box)
Displays image list scanned for 'Aiarty Image Enhancer（画质增强）'.
Supports '只显示有效' checkbox.
Filters images matching: [逻辑父文件夹名]__[纯数字序号].png
"""
from typing import List
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QTableWidgetItem, QSizePolicy
)
from qfluentwidgets import (
    TableWidget, SubtitleLabel, CaptionLabel, PushButton, FluentIcon,
    CheckBox, isDarkTheme, IndeterminateProgressBar
)

from src.config import EnhancerImageItem
from src.ui.pages.enhancer_rule_dialog import show_enhancer_rule_example


class EnhancerResultTableWidget(QWidget):
    """画质增强：模块1右侧图片列表"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_items: List[EnhancerImageItem] = []

        self._init_ui()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 头部标题、统计信息与筛选控制容器（定高，避免未展示表格时被垂直拉伸变形）
        self.header_widget = QWidget(self)
        self.header_widget.setFixedHeight(32)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.title_label = SubtitleLabel("图片列表", self.header_widget)
        header_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.count_label = CaptionLabel("(0 项)", self.header_widget)
        header_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # “只显示有效”复选框（默认不勾选）
        self.only_valid_checkbox = CheckBox("只显示有效", self.header_widget)
        self.only_valid_checkbox.setChecked(False)
        self.only_valid_checkbox.setToolTip("勾选后仅展示符合命名规则的有效数据")
        self.only_valid_checkbox.stateChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.only_valid_checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)

        header_layout.addStretch()

        # 规则说明胶囊标签
        self.rule_tag = CaptionLabel("规则: [逻辑父名]__[纯数字序号].png", self.header_widget)
        self.rule_tag.setToolTip(
            "筛选规则解析：\n"
            "1. 扩展名必须为 .png\n"
            "2. 紧接纯数字序号（如 1, 0123）\n"
            "3. 连续双下划线 '__' 分隔\n"
            "4. 逻辑父名: [字母+纯数字]-[纯数字] (如 B0-001)"
        )
        header_layout.addWidget(self.rule_tag, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 规则示例按钮
        self.rule_example_btn = PushButton(FluentIcon.INFO, "规则示例", self.header_widget)
        self.rule_example_btn.setFixedHeight(28)
        self.rule_example_btn.clicked.connect(self._show_rule_example)
        header_layout.addWidget(self.rule_example_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.header_widget)

        # 进度指示器
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 图片列表表格（5列展示：序号、所在子文件夹、原文件名、逻辑父文件夹名、处理状态）
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        headers = [
            "序号", "所在子文件夹", "原文件名", "逻辑父文件夹名", "处理状态"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectRightClickedRow(True)

        self.table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(2).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(3).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeaderItem(4).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(1, 190)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 90)

        layout.addWidget(self.table, stretch=1)

        # 空状态提示（设置 Expanding 尺寸策略，占据剩余可用高度）
        self.empty_label = QLabel(
            "暂无扫描结果\n请在左侧拖入子文件夹并点击【开始扫描】\n将自动列出所有图片并标记「有效」或「无效」",
            self
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.empty_label, stretch=1)

        # 底部操作栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.status_info = CaptionLabel("就绪", self)
        bottom_layout.addWidget(self.status_info, stretch=1)

        self.clear_table_btn = PushButton(FluentIcon.DELETE, "清空结果", self)
        self.clear_table_btn.setFixedHeight(34)
        self.clear_table_btn.clicked.connect(self.clear_results)
        bottom_layout.addWidget(self.clear_table_btn)

        layout.addLayout(bottom_layout)

        self._update_view()

    def _show_rule_example(self):
        show_enhancer_rule_example(self.rule_example_btn, self.window())

    def _get_displayed_items(self) -> List[EnhancerImageItem]:
        if self.only_valid_checkbox.isChecked():
            return [it for it in self.image_items if it.is_valid]
        return self.image_items

    def _on_filter_changed(self):
        self._refresh_table_rows()

    def set_loading(self, loading: bool):
        if loading:
            self.progress_bar.show()
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.hide()
            self._update_view()

    def set_results(self, items: List[EnhancerImageItem]):
        self.image_items = items
        self._refresh_table_rows()

    def _refresh_table_rows(self):
        self.table.setRowCount(0)
        is_dark = isDarkTheme()

        text_color = QColor("#ffffff" if is_dark else "#1a1a1a")
        accent_blue = QColor("#60cdff" if is_dark else "#0078d4")
        vivid_red = QColor("#ff4d4f" if is_dark else "#e81123")
        muted_color = QColor("#8c8c8c" if is_dark else "#8c8c8c")

        displayed = self._get_displayed_items()

        for row, item in enumerate(displayed):
            self.table.insertRow(row)

            # 0. 序号
            item_idx = QTableWidgetItem(str(row + 1))
            item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_idx.setForeground(QBrush(text_color if item.is_valid else muted_color))
            self.table.setItem(row, 0, item_idx)

            # 1. 所在子文件夹
            item_folder = QTableWidgetItem(item.folder_display_name)
            item_folder.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_folder.setForeground(QBrush(text_color if item.is_valid else muted_color))
            item_folder.setToolTip(f"完整路径：\n{item.folder_path}")
            self.table.setItem(row, 1, item_folder)

            # 2. 原文件名
            item_name = QTableWidgetItem(item.original_name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_name.setForeground(QBrush(text_color if item.is_valid else muted_color))
            if not item.is_valid:
                item_name.setToolTip(f"该图片不符合筛选规则：{item.invalid_reason}")
            else:
                item_name.setToolTip(f"文件路径：\n{item.file_path}")
            self.table.setItem(row, 2, item_name)

            # 3. 逻辑父文件夹名
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

            # 4. 处理状态
            item_status = QTableWidgetItem(item.status_message)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if item.is_valid:
                item_status.setForeground(QBrush(accent_blue))
            else:
                item_status.setForeground(QBrush(vivid_red))
                item_status.setToolTip(f"原因：{item.invalid_reason}")
            f = item_status.font()
            f.setBold(True)
            item_status.setFont(f)
            self.table.setItem(row, 4, item_status)

        self._adjust_column_widths()
        self._update_view()

    def _adjust_column_widths(self):
        self.table.resizeColumnToContents(1)
        w1 = max(190, self.table.columnWidth(1) + 24)
        self.table.setColumnWidth(1, w1)

    def clear_results(self):
        self.image_items.clear()
        self.table.setRowCount(0)
        self.status_info.setText("结果已清空")
        self._update_view()

    def _update_view(self):
        total = len(self.image_items)
        valid_count = sum(1 for it in self.image_items if it.is_valid)
        invalid_count = total - valid_count
        displayed = len(self._get_displayed_items())

        if total > 0:
            if self.only_valid_checkbox.isChecked():
                self.count_label.setText(f"(已筛选: {displayed} 项 · 总计: {total} 项)")
            else:
                self.count_label.setText(f"(共 {total} 项 · 有效: {valid_count} · 无效: {invalid_count})")
        else:
            self.count_label.setText("(0 项)")

        has_items = displayed > 0
        self.table.setVisible(has_items)
        self.empty_label.setVisible(not has_items)
        self.clear_table_btn.setEnabled(total > 0)

    def update_theme(self, is_dark: bool):
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
                QTableView::item { padding: 4px 8px; }
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
            self.empty_label.setStyleSheet("color: rgba(0, 0, 0, 0.45); font-size: 14px; line-height: 1.6;")
            self.table.setStyleSheet("""
                QTableView {
                    background-color: transparent;
                    color: #1a1a1a;
                    gridline-color: rgba(0, 0, 0, 0.06);
                }
                QTableView::item { padding: 4px 8px; }
                QHeaderView::section {
                    color: rgba(0, 0, 0, 0.75);
                    background-color: rgba(0, 0, 0, 0.02);
                    font-weight: 600;
                    padding-left: 8px;
                    padding-right: 8px;
                }
            """)
        self._refresh_table_rows()

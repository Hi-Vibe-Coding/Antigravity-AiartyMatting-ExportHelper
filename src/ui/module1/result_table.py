"""
Result Table & Action Area (Module 1 Right Box)
Displays recognized images matching the special mechanism, computed logical parent names,
and offers one-click batch renaming.
"""
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QHeaderView, QTableWidgetItem
)
from qfluentwidgets import (
    TableWidget, PrimaryPushButton, PushButton, IndeterminateProgressBar,
    FluentIcon, SubtitleLabel, CaptionLabel, InfoBar, InfoBarPosition,
    StrongBodyLabel
)

from src.config import MatchedImageItem


class ResultTableWidget(QFrame):
    """
    模块1右侧结果区：表格呈现与批量操作
    """
    rename_requested = Signal(list)  # List[MatchedImageItem]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.matched_items: List[MatchedImageItem] = []
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("resultTableFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 头部标题与统计信息
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.title_label = SubtitleLabel("匹配图片与逻辑命名列表")
        header_layout.addWidget(self.title_label)

        self.count_label = CaptionLabel("(0 项)")
        self.count_label.setStyleSheet("color: rgba(128, 128, 128, 0.9); font-weight: 500;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # 规则说明胶囊标签
        rule_tag = CaptionLabel("匹配规则: *{name}_attr1_subject.{ext} → 提取逻辑名: {name}")
        rule_tag.setStyleSheet("""
            background-color: rgba(0, 120, 212, 0.1);
            color: #0078d4;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        """)
        header_layout.addWidget(rule_tag)

        layout.addLayout(header_layout)

        # 进度指示器（扫描时显示）
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 结果表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "序号", "所在子文件夹", "原文件名", "逻辑父文件夹名称", "重命名预览", "处理状态"
        ])
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectRightClickedRow(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table, stretch=1)

        # 空状态占位提示
        self.empty_label = QLabel("暂无扫描结果\n请在左侧拖入子文件夹并点击【开始扫描】", self)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: rgba(128, 128, 128, 0.7); font-size: 14px; line-height: 1.6;")
        layout.addWidget(self.empty_label)

        # 底部操作栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.status_info = StrongBodyLabel("")
        bottom_layout.addWidget(self.status_info)

        bottom_layout.addStretch()

        self.clear_table_btn = PushButton(FluentIcon.DELETE, "清空结果", self)
        self.clear_table_btn.setFixedHeight(34)
        self.clear_table_btn.clicked.connect(self.clear_results)
        bottom_layout.addWidget(self.clear_table_btn)

        self.rename_btn = PrimaryPushButton(FluentIcon.EDIT, "一键应用重命名", self)
        self.rename_btn.setFixedHeight(34)
        self.rename_btn.clicked.connect(self._on_rename_clicked)
        bottom_layout.addWidget(self.rename_btn)

        layout.addLayout(bottom_layout)

        self._update_view()

    def set_loading(self, loading: bool):
        if loading:
            self.progress_bar.show()
            self.progress_bar.start()
            self.rename_btn.setEnabled(False)
        else:
            self.progress_bar.stop()
            self.progress_bar.hide()
            self.rename_btn.setEnabled(len(self.matched_items) > 0)

    def set_results(self, items: List[MatchedImageItem]):
        self.matched_items = items
        self.table.setRowCount(0)

        for row, item in enumerate(items):
            self.table.insertRow(row)

            # 序号
            item_idx = QTableWidgetItem(str(row + 1))
            item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_idx)

            # 所在子文件夹
            item_folder = QTableWidgetItem(item.folder_path.name)
            self.table.setItem(row, 1, item_folder)

            # 原文件名
            item_orig = QTableWidgetItem(item.original_name)
            self.table.setItem(row, 2, item_orig)

            # 提取的逻辑父文件夹名称
            item_logic = QTableWidgetItem(item.logical_parent)
            item_logic.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item_logic)

            # 重命名目标预览
            item_target = QTableWidgetItem(item.target_name)
            self.table.setItem(row, 4, item_target)

            # 处理状态
            item_status = QTableWidgetItem(item.status_message)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, item_status)

        self._update_view()

    def update_rename_progress(self, current: int, total: int, filename: str):
        self.status_info.setText(f"正在重命名 ({current}/{total}): {filename}")

    def update_rename_results(self, success_count: int, fail_count: int, items: List[MatchedImageItem]):
        self.set_results(items)
        self.status_info.setText(f"重命名完成：成功 {success_count} 个，失败 {fail_count} 个")

    def clear_results(self):
        self.matched_items.clear()
        self.table.setRowCount(0)
        self.status_info.setText("")
        self._update_view()

    def _update_view(self):
        count = len(self.matched_items)
        self.count_label.setText(f"({count} 项)")

        has_items = count > 0
        self.table.setVisible(has_items)
        self.empty_label.setVisible(not has_items)
        self.rename_btn.setEnabled(has_items)
        self.clear_table_btn.setEnabled(has_items)

    def _on_rename_clicked(self):
        if not self.matched_items:
            return
        self.rename_requested.emit(self.matched_items)

"""
Area 1 / Module 1 Composite Widget
Combines FolderDropZoneWidget (left) and ResultTableWidget (right).
Handles asynchronous scanning and renaming via QThreadPool.
"""
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, InfoBar, InfoBarPosition
)

from src.config import MatchedImageItem
from src.core.scanner import FolderScannerWorker
from src.core.renamer import FileRenamerWorker
from src.ui.module1.folder_drop_zone import FolderDropZoneWidget
from src.ui.module1.result_table import ResultTableWidget


class Module1Widget(CardWidget):
    """
    区域1 / 模块1 主容器卡片
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.current_scan_worker = None
        self.current_rename_worker = None

        self._init_ui()
        self._bind_events()

    def _init_ui(self):
        self.setObjectName("module1Widget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        # 区域1标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = TitleLabel("模块 1：特殊命名图片识别与逻辑重命名")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(title)

        desc = CaptionLabel("支持子文件夹拖拽识别，精准捕获 *_attr1_subject 目标图片并提取逻辑父名称")
        desc.setStyleSheet("color: rgba(128, 128, 128, 0.85); margin-top: 4px;")
        header_layout.addWidget(desc)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 左右两栏布局（使用 Splitter，用户可自由拖拽调整左右比例）
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setHandleWidth(8)

        # 左侧：子文件夹拖拽区
        self.left_drop_zone = FolderDropZoneWidget(self.splitter)
        self.left_drop_zone.setMinimumWidth(320)

        # 右侧：识别结果区
        self.right_result_table = ResultTableWidget(self.splitter)
        self.right_result_table.setMinimumWidth(500)

        self.splitter.addWidget(self.left_drop_zone)
        self.splitter.addWidget(self.right_result_table)

        # 设置左右宽度比为 3.5 : 6.5
        self.splitter.setSizes([380, 720])

        layout.addWidget(self.splitter, stretch=1)

    def _bind_events(self):
        # 扫描事件
        self.left_drop_zone.start_scan_requested.connect(self._start_scanning)
        # 重命名事件
        self.right_result_table.rename_requested.connect(self._start_renaming)

    def _start_scanning(self, folder_paths: List[Path]):
        self.right_result_table.set_loading(True)
        self.right_result_table.status_info.setText("正在扫描图片...")

        worker = FolderScannerWorker(folder_paths)
        worker.signals.progress.connect(self._on_scan_progress)
        worker.signals.finished.connect(self._on_scan_finished)
        worker.signals.error.connect(self._on_scan_error)

        self.current_scan_worker = worker
        self.thread_pool.start(worker)

    def _on_scan_progress(self, current: int, total: int, folder_name: str):
        self.right_result_table.status_info.setText(
            f"正在扫描目录 ({current}/{total}): {folder_name}"
        )

    def _on_scan_finished(self, matched_items: List[MatchedImageItem]):
        self.right_result_table.set_loading(False)
        self.right_result_table.set_results(matched_items)

        count = len(matched_items)
        if count == 0:
            self.right_result_table.status_info.setText("扫描完成：未发现匹配的特殊命名图片")
            InfoBar.info(
                title="扫描完成",
                content="所选子文件夹中未找到以 '_attr1_subject' 命名的有效图片。",
                parent=self.window(),
                duration=3000,
                position=InfoBarPosition.TOP
            )
        else:
            self.right_result_table.status_info.setText(f"扫描完成：共发现 {count} 张有效图片")
            InfoBar.success(
                title="扫描成功",
                content=f"共找出 {count} 张符合规则的图片，并已计算逻辑父名称！",
                parent=self.window(),
                duration=2500,
                position=InfoBarPosition.TOP
            )

    def _on_scan_error(self, err_msg: str):
        self.right_result_table.set_loading(False)
        InfoBar.error(
            title="扫描出错",
            content=f"扫描过程中发生异常: {err_msg}",
            parent=self.window(),
            duration=4000,
            position=InfoBarPosition.TOP
        )

    def _start_renaming(self, items: List[MatchedImageItem]):
        if not items:
            return

        self.right_result_table.set_loading(True)
        worker = FileRenamerWorker(items)
        worker.signals.progress.connect(self.right_result_table.update_rename_progress)
        worker.signals.finished.connect(self._on_rename_finished)
        worker.signals.error.connect(self._on_rename_error)

        self.current_rename_worker = worker
        self.thread_pool.start(worker)

    def _on_rename_finished(self, success_count: int, fail_count: int, items: List[MatchedImageItem]):
        self.right_result_table.set_loading(False)
        self.right_result_table.update_rename_results(success_count, fail_count, items)

        if fail_count == 0:
            InfoBar.success(
                title="重命名完成",
                content=f"全部 {success_count} 个图片文件已成功更名！",
                parent=self.window(),
                duration=3000,
                position=InfoBarPosition.TOP
            )
        else:
            InfoBar.warning(
                title="部分重命名未完成",
                content=f"成功: {success_count} 个，失败/冲突: {fail_count} 个，请检查表格状态。",
                parent=self.window(),
                duration=4000,
                position=InfoBarPosition.TOP
            )

    def _on_rename_error(self, err_msg: str):
        self.right_result_table.set_loading(False)
        InfoBar.error(
            title="重命名出错",
            content=f"重命名过程中发生错误: {err_msg}",
            parent=self.window(),
            duration=4000,
            position=InfoBarPosition.TOP
        )

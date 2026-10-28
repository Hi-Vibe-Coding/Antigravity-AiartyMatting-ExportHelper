"""
Area 1 / Module 1 Composite Widget
Combines FolderDropZoneWidget (left) and ResultTableWidget (right).
Handles asynchronous scanning and renaming via QThreadPool.
"""
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, InfoBar, InfoBarPosition, isDarkTheme
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
    folder_list_modified = Signal()  # 当模块1的子文件夹发生变动时发出信号，通知外部重置模块2
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.current_scan_worker = None
        self.current_rename_worker = None

        self._init_ui()
        self._bind_events()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        self.setObjectName("module1Widget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        # 区域1标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title = TitleLabel("模块 1：特殊命名图片识别", self)
        self.title.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.desc = CaptionLabel("支持子文件夹拖拽识别，完整列出目录图片，区分有效「待重命名」与「无效」文件", self)
        header_layout.addWidget(self.desc)
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
        self.splitter.setSizes([360, 740])

        layout.addWidget(self.splitter, stretch=1)

    def update_theme(self, is_dark: bool):
        """同步子组件与自身的深浅主题配色"""
        if is_dark:
            self.desc.setStyleSheet("color: rgba(255, 255, 255, 0.65); margin-top: 4px;")
        else:
            self.desc.setStyleSheet("color: rgba(0, 0, 0, 0.55); margin-top: 4px;")

        self.left_drop_zone.update_theme(is_dark)
        self.right_result_table.update_theme(is_dark)

    def _bind_events(self):
        self.left_drop_zone.start_scan_requested.connect(self._start_scanning)
        self.left_drop_zone.folder_added.connect(self._on_folder_changed)
        self.left_drop_zone.folder_removed.connect(self._on_folder_changed)
        self.left_drop_zone.folders_cleared.connect(self._on_folder_changed)
        self.right_result_table.rename_requested.connect(self._start_renaming)

    def _on_folder_changed(self, *args):
        """需求：每当拖入一个新的子文件夹(或移除一个子文件夹)，右侧数据列表就刷新为空，且通知外部重置模块2"""
        self.right_result_table.clear_results()
        self.folder_list_modified.emit()

    def _start_scanning(self, folder_paths: List[Path], recursive: bool = True):
        self.right_result_table.set_loading(True)
        scan_mode_desc = " (递归扫描)" if recursive else ""
        self.right_result_table.status_info.setText(f"正在扫描图片{scan_mode_desc}...")

        worker = FolderScannerWorker(folder_paths, recursive=recursive)
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

        total_count = len(matched_items)
        valid_count = sum(1 for it in matched_items if it.is_valid)
        invalid_count = total_count - valid_count

        if total_count == 0:
            self.right_result_table.status_info.setText("扫描完成：文件夹内未发现图片文件")
            InfoBar.info(
                title="扫描完成",
                content="所选子文件夹中未找到任何图片文件。",
                parent=self.window(),
                duration=3000,
                position=InfoBarPosition.TOP
            )
        elif valid_count == 0:
            self.right_result_table.status_info.setText(f"扫描完成：共 {total_count} 张图片，均不符合规则（全部为无效）")
            InfoBar.warning(
                title="未发现有效图片",
                content=f"共扫描到 {total_count} 张图片，但全部为「无效」状态（未匹配特殊机制命名规则）。",
                parent=self.window(),
                duration=3500,
                position=InfoBarPosition.TOP
            )
        else:
            self.right_result_table.status_info.setText(
                f"扫描完成：共 {total_count} 张图片（有效 {valid_count} 张，无效 {invalid_count} 张）"
            )
            InfoBar.success(
                title="扫描成功",
                content=f"共发现 {total_count} 张图片，其中 {valid_count} 张为有效图片（待重命名）！",
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
        valid_items = [it for it in items if it.is_valid and not it.is_renamed]
        if not valid_items:
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
                content=f"全部 {success_count} 个有效文件已成功更名！",
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

"""
Folder scanner & image matching engine with QThread worker.
"""
from pathlib import Path
from typing import List
import re

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool

from src.config import (
    SUPPORTED_IMAGE_EXTENSIONS,
    DEFAULT_SPECIAL_SUFFIX,
    MatchedImageItem,
    build_pattern,
)


class ScanSignals(QObject):
    """扫描器信号集"""
    progress = Signal(int, int, str)               # current, total, current_folder_name
    item_found = Signal(object)                    # MatchedImageItem
    finished = Signal(list)                        # List[MatchedImageItem]
    error = Signal(str)


class FolderScannerWorker(QRunnable):
    """后台异步扫描工作线程"""
    def __init__(self, folder_paths: List[Path], suffix: str = DEFAULT_SPECIAL_SUFFIX):
        super().__init__()
        self.folder_paths = folder_paths
        self.suffix = suffix
        self.pattern = build_pattern(suffix)
        self.signals = ScanSignals()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        matched_items: List[MatchedImageItem] = []
        total_folders = len(self.folder_paths)

        try:
            for idx, folder_path in enumerate(self.folder_paths, start=1):
                if self._is_cancelled:
                    break

                folder_name = folder_path.name
                self.signals.progress.emit(idx, total_folders, folder_name)

                if not folder_path.exists() or not folder_path.is_dir():
                    continue

                # 遍历当前子文件夹内的直接文件（非递归或浅层遍历）
                try:
                    for entry in folder_path.iterdir():
                        if self._is_cancelled:
                            break

                        if not entry.is_file():
                            continue

                        ext = entry.suffix.lower()
                        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
                            continue

                        match = self.pattern.match(entry.name)
                        if match:
                            logical_parent = match.group("logical_parent")
                            matched_ext = match.group("ext")
                            # 默认目标新名称：例如 AAA.png (去除特殊后缀)
                            target_name = f"{logical_parent}{matched_ext}"

                            item = MatchedImageItem(
                                file_path=entry,
                                folder_path=folder_path,
                                original_name=entry.name,
                                logical_parent=logical_parent,
                                extension=matched_ext,
                                target_name=target_name,
                                is_renamed=False,
                                status_message="待重命名"
                            )
                            matched_items.append(item)
                            self.signals.item_found.emit(item)
                except Exception as inner_e:
                    # 单个文件夹读取权限或IO异常
                    continue

            self.signals.finished.emit(matched_items)
        except Exception as e:
            self.signals.error.emit(str(e))

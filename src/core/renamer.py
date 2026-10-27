"""
File renaming worker and utilities.
"""
from pathlib import Path
from typing import List, Tuple
from PySide6.QtCore import QObject, Signal, QRunnable

from src.config import MatchedImageItem


class RenameSignals(QObject):
    progress = Signal(int, int, str)               # current, total, filename
    finished = Signal(int, int, list)              # success_count, fail_count, updated_items
    error = Signal(str)


class FileRenamerWorker(QRunnable):
    """后台异步执行重命名任务"""
    def __init__(self, items: List[MatchedImageItem], overwrite: bool = False):
        super().__init__()
        self.items = items
        self.overwrite = overwrite
        self.signals = RenameSignals()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        success_count = 0
        fail_count = 0
        total = len(self.items)

        try:
            for idx, item in enumerate(self.items, start=1):
                if self._is_cancelled:
                    break

                self.signals.progress.emit(idx, total, item.original_name)

                if item.is_renamed:
                    continue

                source_path = item.file_path
                target_path = item.folder_path / item.target_name

                if not source_path.exists():
                    item.status_message = "原文件不存在"
                    fail_count += 1
                    continue

                if target_path.exists() and not self.overwrite:
                    if target_path != source_path:
                        item.status_message = f"目标已存在: {item.target_name}"
                        fail_count += 1
                        continue

                try:
                    # 执行安全重命名
                    new_path = source_path.rename(target_path)
                    item.file_path = new_path
                    item.is_renamed = True
                    item.status_message = "重命名成功"
                    success_count += 1
                except Exception as e:
                    item.status_message = f"重命名失败: {str(e)}"
                    fail_count += 1

            self.signals.finished.emit(success_count, fail_count, self.items)
        except Exception as e:
            self.signals.error.emit(str(e))

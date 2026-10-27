"""
Folder scanner & image matching engine with QThread worker.
Scans ALL image files in the folders and categorizes them as valid or invalid.
Supports both shallow (1-level) and recursive (deep nested) scanning.
Accurately computes upper-level display paths for '所在子文件夹' (e.g. Batch_Export_案例3\新建文件夹).
"""
import os
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal, QRunnable

from src.config import (
    ALL_IMAGE_EXTENSIONS,
    IMAGE_PATTERN,
    MatchedImageItem,
)


class ScanSignals(QObject):
    """扫描器信号集"""
    progress = Signal(int, int, str)               # current, total, current_folder_name
    item_found = Signal(object)                    # MatchedImageItem
    finished = Signal(list)                        # List[MatchedImageItem]
    error = Signal(str)


class FolderScannerWorker(QRunnable):
    """后台异步扫描工作线程"""
    def __init__(self, folder_paths: List[Path], recursive: bool = True):
        super().__init__()
        self.folder_paths = folder_paths
        self.recursive = recursive
        self.signals = ScanSignals()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        scanned_items: List[MatchedImageItem] = []
        total_folders = len(self.folder_paths)

        try:
            for idx, folder_path in enumerate(self.folder_paths, start=1):
                if self._is_cancelled:
                    break

                folder_name = folder_path.name
                scan_mode_tag = " [递归]" if self.recursive else ""
                self.signals.progress.emit(idx, total_folders, f"{folder_name}{scan_mode_tag}")

                if not folder_path.exists() or not folder_path.is_dir():
                    continue

                try:
                    entries: List[Path] = []
                    if self.recursive:
                        # 递归遍历所有内置多层嵌套文件夹
                        for root, _, files in os.walk(folder_path):
                            if self._is_cancelled:
                                break
                            root_path = Path(root)
                            for file_name in files:
                                entries.append(root_path / file_name)
                    else:
                        # 仅扫描当前子文件夹直属第 1 层
                        for p in folder_path.iterdir():
                            if p.is_file():
                                entries.append(p)

                    # 按文件名自然排序
                    entries.sort(key=lambda e: e.name.lower())

                    for entry in entries:
                        if self._is_cancelled:
                            break

                        ext = entry.suffix.lower()
                        # 仅扫描图片类型文件
                        if ext not in ALL_IMAGE_EXTENSIONS:
                            continue

                        # 实际所在物理子文件夹（确保重命名发生在所属真实路径）
                        actual_folder = entry.parent

                        # 精准向上计算展示路径（例如 Batch_Export_案例3 或 Batch_Export_案例3\新建文件夹）
                        try:
                            folder_display_name = str(entry.parent.relative_to(folder_path.parent))
                        except Exception:
                            folder_display_name = entry.parent.name

                        match = IMAGE_PATTERN.match(entry.name)
                        if match:
                            logical_parent = match.group("logical_parent")
                            seq = match.group("seq")
                            matched_ext = match.group("ext")
                            target_name = f"{logical_parent}__{seq}{matched_ext}"

                            item = MatchedImageItem(
                                file_path=entry,
                                folder_path=actual_folder,
                                folder_display_name=folder_display_name,
                                original_name=entry.name,
                                is_valid=True,
                                logical_parent=logical_parent,
                                sequence_num=seq,
                                extension=matched_ext,
                                target_name=target_name,
                                is_renamed=False,
                                status_message="待重命名",
                                invalid_reason=""
                            )
                        else:
                            reason = "格式非 .png" if ext != ".png" else "命名不符合规则"
                            item = MatchedImageItem(
                                file_path=entry,
                                folder_path=actual_folder,
                                folder_display_name=folder_display_name,
                                original_name=entry.name,
                                is_valid=False,
                                logical_parent="-",
                                sequence_num="-",
                                extension=ext,
                                target_name="-",
                                is_renamed=False,
                                status_message="无效",
                                invalid_reason=reason
                            )

                        scanned_items.append(item)
                        self.signals.item_found.emit(item)
                except Exception as inner_e:
                    continue

            self.signals.finished.emit(scanned_items)
        except Exception as e:
            self.signals.error.emit(str(e))

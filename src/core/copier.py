"""
File Copier Worker and Utilities for Module 2.
Safely copies matched files from Module 1 to their respective destination directories in Module 2.
Provides real-time progress and detailed success/fail callbacks.
"""
import shutil
from pathlib import Path
from typing import List
from PySide6.QtCore import QObject, Signal, QRunnable

from src.core.tracer import LogicalTraceItem
from src.core.logger import logger


class CopierSignals(QObject):
    progress = Signal(int, int, str)               # current, total, filename/description
    finished = Signal(int, int, list)              # success_count, fail_count, updated_items
    error = Signal(str)                            # error message


class FileCopierWorker(QRunnable):
    """
    后台异步执行文件复制任务：
    - 针对数据对照表中有效的目标路径（即 status_type 为 normal 或 override 的项）
    - 将原图片复制到对应的目标同名逻辑父文件夹中，命名为预期重命名
    - 汇报实时进度与结果
    """
    def __init__(self, trace_items: List[LogicalTraceItem]):
        super().__init__()
        self.trace_items = trace_items
        self.signals = CopierSignals()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        # 筛选出有明确目标路径的可复制项
        copyable_items = [
            it for it in self.trace_items
            if it.matched_target_folder and it.dest_file_path and it.full_source_file
        ]
        total = len(copyable_items)

        if total == 0:
            self.signals.finished.emit(0, 0, self.trace_items)
            return

        success_count = 0
        fail_count = 0

        logger.info(f"开始后台执行文件复制任务，共 {total} 个待复制文件")

        for idx, item in enumerate(copyable_items, start=1):
            if self._is_cancelled:
                logger.warning("文件复制任务被用户取消")
                break

            src = item.full_source_file
            dst = item.dest_file_path

            self.signals.progress.emit(idx, total, f"{src.name} -> {item.dest_folder_display}")

            try:
                if not src.exists():
                    logger.error(f"复制失败：源文件不存在: {src}")
                    item.status_display = "源文件不存在"
                    item.status_type = "error"
                    fail_count += 1
                    continue

                # 确保目标父文件夹存在
                dst.parent.mkdir(parents=True, exist_ok=True)

                # 执行文件复制（保持元数据）
                shutil.copy2(src, dst)

                # 复制成功，更新状态
                item.status_display = f"已成功写入到[{item.dest_folder_display}]"
                item.status_type = "normal"
                item.is_copied = True
                success_count += 1
                logger.debug(f"已成功复制: {src.name} -> {dst}")

            except Exception as e:
                logger.error(f"复制文件异常: {src} -> {dst}, 原因: {e}")
                item.status_display = f"写入失败: {e}"
                item.status_type = "error"
                fail_count += 1

        logger.info(f"文件复制任务完成：成功 {success_count} 个，失败 {fail_count} 个")
        self.signals.finished.emit(success_count, fail_count, self.trace_items)

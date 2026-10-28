"""
Area 2 / Module 2 Widget: '溯源到父文件夹'
Combines SingleFolderDropZone (left) and TraceResultTableWidget (right).
Inherits semi-transparent lock mask overlay logic.
"""
import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QStackedLayout
)
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, StrongBodyLabel, FluentIcon, IconWidget,
    InfoBar, InfoBarPosition, isDarkTheme
)

from src.config import MatchedImageItem
from src.core.tracer import LogicalTraceItem, format_relative_path
from src.core.copier import FileCopierWorker
from src.ui.module2.single_folder_drop_zone import SingleFolderDropZone
from src.ui.module2.trace_result_table import TraceResultTableWidget


class Module2Widget(CardWidget):
    """
    模块 2：溯源到父文件夹
    - 左侧：单文件夹拖拽区（模块2的源文件夹）+ 开始分析按钮
    - 右侧：专属数据表格（序号、原文件名、逻辑父文件夹、目标重命名、状态字段[已匹配/无法找到]）
    - 维持半透明锁定遮罩（未点击转移前锁定）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_locked = True
        self.setMinimumHeight(520)
        self.thread_pool = QThreadPool.globalInstance()
        self.current_copier_worker = None

        # 缓存从外部/模块1传入的有效图片项数据源
        self.source_module1_items: List[MatchedImageItem] = []

        self._init_ui()
        self._bind_events()
        self.set_locked(True)
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        self.setObjectName("module2Widget")

        # 核心层叠布局：半透明浮层覆盖
        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # 0 层：实际内容层
        self.content_widget = QWidget(self)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(18, 16, 18, 18)
        content_layout.setSpacing(14)

        # 标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title = TitleLabel("模块 2：溯源到父文件夹", self.content_widget)
        self.title.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.desc = CaptionLabel("根据模块1解析出的逻辑父文件夹，在目标源文件夹中溯源匹配同名真实文件夹", self.content_widget)
        header_layout.addWidget(self.desc)
        header_layout.addStretch()

        content_layout.addLayout(header_layout)

        # 左右两栏 Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.content_widget)
        self.splitter.setHandleWidth(8)

        # 左侧：单文件夹拖拽区
        self.left_drop_zone = SingleFolderDropZone(self.splitter)
        self.left_drop_zone.setMinimumWidth(320)

        # 右侧：专属数据结果表格
        self.right_table = TraceResultTableWidget(self.splitter)
        self.right_table.setMinimumWidth(520)

        self.splitter.addWidget(self.left_drop_zone)
        self.splitter.addWidget(self.right_table)
        self.splitter.setSizes([360, 740])

        content_layout.addWidget(self.splitter, stretch=1)
        self.stacked_layout.addWidget(self.content_widget)

        # 1 层：半透明遮罩层
        self.mask_overlay = QFrame(self)
        self.mask_overlay.setObjectName("module2MaskOverlay")
        mask_layout = QVBoxLayout(self.mask_overlay)
        mask_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mask_layout.setSpacing(12)

        self.mask_icon = IconWidget(FluentIcon.HIDE, self.mask_overlay)
        self.mask_icon.setFixedSize(52, 52)
        mask_layout.addWidget(self.mask_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.mask_title = StrongBodyLabel("模块 2 处于待命锁定状态", self.mask_overlay)
        self.mask_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mask_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        mask_layout.addWidget(self.mask_title)

        self.mask_desc = CaptionLabel("请先在上方核对扫描结果，并点击【准备复制到[逻辑父文件夹]】解锁此区域", self.mask_overlay)
        self.mask_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mask_layout.addWidget(self.mask_desc)

        self.stacked_layout.addWidget(self.mask_overlay)

    def _bind_events(self):
        self.left_drop_zone.start_analyze_requested.connect(self._run_analysis)
        self.left_drop_zone.folder_selected.connect(self._on_source_folder_changed)
        self.left_drop_zone.folder_cleared.connect(self._on_source_folder_changed)
        self.right_table.copy_requested.connect(self._start_copying)

    def _start_copying(self):
        """响应点击“开始复制”操作：在后台线程中逐一复制文件并反馈实时进度"""
        items_to_copy = self.right_table.trace_items
        valid_items = [
            it for it in items_to_copy
            if it.matched_target_folder and it.dest_file_path and it.full_source_file
        ]

        if not valid_items:
            InfoBar.warning(
                title="无有效复制项",
                content="当前列表中没有可唯一定位写入目标的有效图片！",
                parent=self,
                duration=3500,
                position=InfoBarPosition.TOP
            )
            return

        self.right_table.set_copying_state(True)

        worker = FileCopierWorker(items_to_copy)
        worker.signals.progress.connect(self._on_copy_progress)
        worker.signals.finished.connect(self._on_copy_finished)
        worker.signals.error.connect(self._on_copy_error)

        self.current_copier_worker = worker
        self.thread_pool.start(worker)

    def _on_copy_progress(self, current: int, total: int, filename: str):
        self.right_table.update_copy_progress(current, total, filename)

    def _on_copy_finished(self, success_count: int, fail_count: int, items: List[LogicalTraceItem]):
        self.right_table.update_copy_finished(success_count, fail_count, items)
        self.current_copier_worker = None

        # 需求：复制结束后，飘字提醒
        if fail_count == 0:
            InfoBar.success(
                title="复制完成",
                content=f"恭喜！全部 {success_count} 张图片已成功复制到目标逻辑父文件夹！",
                parent=self.window(),
                duration=4500,
                position=InfoBarPosition.TOP
            )
        else:
            InfoBar.warning(
                title="复制完成 (部分失败)",
                content=f"已成功复制 {success_count} 张图片，{fail_count} 张复制失败，请查看列表状态。",
                parent=self.window(),
                duration=5000,
                position=InfoBarPosition.TOP
            )

    def _on_copy_error(self, err_msg: str):
        self.right_table.set_copying_state(False)
        self.current_copier_worker = None
        InfoBar.error(
            title="复制出错",
            content=f"执行复制任务过程中发生错误：{err_msg}",
            parent=self.window(),
            duration=4000,
            position=InfoBarPosition.TOP
        )

    def _on_source_folder_changed(self, *args):
        """需求：每当拖入一个新的源文件夹(或移除一个源文件夹)，则右侧数据列表就刷新为空"""
        self.right_table.clear_results()

    def set_source_items(self, items: List[MatchedImageItem]):
        """接收模块1传递过来的数据列表"""
        self.source_module1_items = items

    def _run_analysis(self, source_folder: Path):
        """
        核心分析逻辑：
        遍历模块1中的数据行，每找到一个“逻辑父文件夹”，
        则在“源文件夹”中查找与“逻辑父文件夹”同名的文件夹：
        1. “源文件夹”自身也可以直接作为逻辑对比（源文件夹名与逻辑父文件夹一致）。
        2. 在源文件夹下递归遍历所有子文件夹查找同名目录：
           - 找到 0 个：状态标记为「无法找到」
           - 找到 1 个：状态标记为「已匹配」
           - 找到 >1 个：状态标记为「同名文件夹不唯一」
        """
        if not source_folder.is_dir():
            InfoBar.error(
                title="源文件夹无效",
                content="指定的目标源文件夹不存在或不是目录！",
                parent=self,
                duration=3500,
                position=InfoBarPosition.TOP
            )
            return

        if not self.source_module1_items:
            InfoBar.warning(
                title="无待分析数据",
                content="模块 1 中暂无有效数据，请先在上方完成扫描！",
                parent=self,
                duration=3500,
                position=InfoBarPosition.TOP
            )
            return

        # 扫描源文件夹自身及其内部所有子文件夹，建立名称映射：name -> List[Path]
        folder_name_map = {}

        def _add_folder(name: str, p: Path):
            if name not in folder_name_map:
                folder_name_map[name] = []
            if p not in folder_name_map[name]:
                folder_name_map[name].append(p)

        try:
            # 1. 源文件夹自身直接作为逻辑对比
            _add_folder(source_folder.name, source_folder)

            # 2. 遍历源文件夹下的子目录
            for root, dirs, _ in os.walk(source_folder):
                for d in dirs:
                    d_path = Path(root) / d
                    _add_folder(d, d_path)
        except Exception as e:
            InfoBar.error(
                title="读取目录失败",
                content=f"无法读取源文件夹：{e}",
                parent=self,
                duration=4000,
                position=InfoBarPosition.TOP
            )
            return

        trace_results: List[LogicalTraceItem] = []

        # 遍历模块1中的有效数据项
        for idx, item in enumerate(self.source_module1_items):
            # 若是无效项则略过（或逻辑父文件夹为空）
            if not item.is_valid or not item.logical_parent or item.logical_parent == "-":
                continue

            # 字段2计算：原文件仅显示纯文件名（如 B0-001__1_attr1_subject.png）
            raw_file_display = item.original_name

            # 字段3计算：预期重命名
            expected_rename = item.target_name

            target_name = item.logical_parent
            # 精确匹配（若无，可尝试不区分大小写查找）
            matches = folder_name_map.get(target_name, [])
            if not matches:
                lower_target = target_name.lower()
                for k, v in folder_name_map.items():
                    if k.lower() == lower_target:
                        matches.extend([p for p in v if p not in matches])

            match_count = len(matches)

            if match_count == 1:
                # 唯一匹配
                matched_folder = matches[0]
                dest_file = matched_folder / expected_rename

                # 检查同名文件夹中是否已有同名图片文件
                # 计算目标路径相对显示（尽可能3层，如：A 预制\Bracelet\B0-001）
                target_folder_display = format_relative_path(matched_folder, max_levels=3)

                if dest_file.exists():
                    status_text = f"即将被写入到[{target_folder_display}](同名文件将覆盖!)"
                    status_type = "override"
                else:
                    status_text = f"即将被写入到[{target_folder_display}]"
                    status_type = "normal"

                trace_item = LogicalTraceItem(
                    original_item_idx=idx + 1,
                    raw_file_display=raw_file_display,
                    expected_rename=expected_rename,
                    logical_parent=item.logical_parent,
                    status_display=status_text,
                    status_type=status_type,
                    full_source_file=item.file_path,
                    matched_target_folder=matched_folder,
                    dest_file_path=dest_file,
                    dest_folder_display=target_folder_display,
                    candidate_folders=matches
                )
            elif match_count > 1:
                # 同名文件夹不唯一
                trace_item = LogicalTraceItem(
                    original_item_idx=idx + 1,
                    raw_file_display=raw_file_display,
                    expected_rename=expected_rename,
                    logical_parent=item.logical_parent,
                    status_display="同名文件夹不唯一",
                    status_type="error",
                    full_source_file=item.file_path,
                    matched_target_folder=None,
                    dest_file_path=None,
                    candidate_folders=matches
                )
            else:
                # 无法找到
                trace_item = LogicalTraceItem(
                    original_item_idx=idx + 1,
                    raw_file_display=raw_file_display,
                    expected_rename=expected_rename,
                    logical_parent=item.logical_parent,
                    status_display="无法找到",
                    status_type="error",
                    full_source_file=item.file_path,
                    matched_target_folder=None,
                    dest_file_path=None,
                    candidate_folders=[]
                )

            trace_results.append(trace_item)

        self.right_table.set_results(trace_results)

        normal_count = sum(1 for it in trace_results if it.status_type == "normal")
        override_count = sum(1 for it in trace_results if it.status_type == "override")
        ambiguous_count = sum(1 for it in trace_results if it.status_display == "同名文件夹不唯一")
        not_found_count = sum(1 for it in trace_results if it.status_display == "无法找到")

        if ambiguous_count > 0 or not_found_count > 0 or override_count > 0:
            msg_parts = []
            if normal_count > 0:
                msg_parts.append(f"{normal_count} 项即将写入")
            if override_count > 0:
                msg_parts.append(f"{override_count} 项同名将覆盖")
            if ambiguous_count > 0:
                msg_parts.append(f"{ambiguous_count} 项同名不唯一")
            if not_found_count > 0:
                msg_parts.append(f"{not_found_count} 项无法找到")

            InfoBar.warning(
                title="分析完成 (需关注状态)",
                content=f"共分析 {len(trace_results)} 条数据：" + "，".join(msg_parts),
                parent=self,
                duration=4500,
                position=InfoBarPosition.TOP
            )
        else:
            InfoBar.success(
                title="分析完成",
                content=f"共分析 {len(trace_results)} 条数据，全部 {normal_count} 项均唯一定位无冲突！",
                parent=self,
                duration=3500,
                position=InfoBarPosition.TOP
            )

    def reset_module(self):
        """
        重置模块2全部数据与状态：
        - 清空左侧选中的源文件夹
        - 清空右侧对照数据列表
        - 清空缓存的模块1有效数据源
        - 重新启用半透明锁定遮罩
        """
        self.source_module1_items.clear()
        self.left_drop_zone.clear_folder()
        self.right_table.clear_results()
        self.set_locked(True)

    def set_locked(self, locked: bool):
        """控制遮罩的显示与内容的交互状态"""
        self.is_locked = locked
        self.mask_overlay.setVisible(locked)
        self.content_widget.setEnabled(not locked)
        if locked:
            self.mask_overlay.raise_()

    def update_theme(self, is_dark: bool):
        """刷新深浅主题的高对比度样式"""
        if is_dark:
            self.desc.setStyleSheet("color: rgba(255, 255, 255, 0.65); margin-top: 4px;")
            self.mask_desc.setStyleSheet("color: rgba(255, 255, 255, 0.65); font-size: 13px;")
            self.mask_overlay.setStyleSheet("""
                QFrame#module2MaskOverlay {
                    background-color: rgba(24, 24, 24, 0.82);
                    border: 1px dashed rgba(255, 255, 255, 0.18);
                    border-radius: 10px;
                }
            """)
        else:
            self.desc.setStyleSheet("color: rgba(0, 0, 0, 0.55); margin-top: 4px;")
            self.mask_desc.setStyleSheet("color: rgba(0, 0, 0, 0.60); font-size: 13px;")
            self.mask_overlay.setStyleSheet("""
                QFrame#module2MaskOverlay {
                    background-color: rgba(248, 249, 250, 0.84);
                    border: 1px dashed rgba(0, 0, 0, 0.15);
                    border-radius: 10px;
                }
            """)

        self.left_drop_zone.update_theme(is_dark)
        self.right_table.update_theme(is_dark)

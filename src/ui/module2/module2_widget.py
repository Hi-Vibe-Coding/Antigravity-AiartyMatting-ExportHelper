"""
Area 2 / Module 2 Widget: '溯源到父文件夹'
Combines SingleFolderDropZone (left) and TraceResultTableWidget (right).
Inherits semi-transparent lock mask overlay logic.
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QStackedLayout
)
from qfluentwidgets import (
    CardWidget, TitleLabel, CaptionLabel, StrongBodyLabel, FluentIcon, IconWidget,
    InfoBar, InfoBarPosition, isDarkTheme
)

from src.config import MatchedImageItem
from src.core.tracer import LogicalTraceItem
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
        则在“模块2的源文件夹”中查找与“逻辑父文件夹”同名的文件夹。
        若找不到，状态标记为“无法找到”；若找到，状态标记为“已匹配”。
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

        # 扫描源文件夹下的所有直接子目录（建立名称映射）
        existing_subdirs = {}
        try:
            for entry in source_folder.iterdir():
                if entry.is_dir():
                    existing_subdirs[entry.name] = entry
                    lower_key = entry.name.lower()
                    if lower_key not in existing_subdirs:
                        existing_subdirs[lower_key] = entry
        except Exception as e:
            InfoBar.error(
                title="读取目录失败",
                content=f"无法读取模块2源文件夹：{e}",
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

            target_folder = existing_subdirs.get(item.logical_parent)
            if not target_folder:
                # 尝试小写查找
                target_folder = existing_subdirs.get(item.logical_parent.lower())

            if target_folder and target_folder.is_dir():
                trace_item = LogicalTraceItem(
                    original_item_idx=idx + 1,
                    original_name=item.original_name,
                    target_name=item.target_name,
                    logical_parent=item.logical_parent,
                    matched_target_folder=target_folder,
                    status="已匹配",
                    is_matched=True
                )
            else:
                trace_item = LogicalTraceItem(
                    original_item_idx=idx + 1,
                    original_name=item.original_name,
                    target_name=item.target_name,
                    logical_parent=item.logical_parent,
                    matched_target_folder=None,
                    status="无法找到",
                    is_matched=False
                )

            trace_results.append(trace_item)

        self.right_table.set_results(trace_results)

        matched_count = sum(1 for it in trace_results if it.is_matched)
        unmatched_count = len(trace_results) - matched_count

        if unmatched_count > 0:
            InfoBar.warning(
                title="分析完成 (含未命中项)",
                content=f"共分析 {len(trace_results)} 条数据：{matched_count} 项成功匹配，{unmatched_count} 项「无法找到」同名文件夹！",
                parent=self,
                duration=4500,
                position=InfoBarPosition.TOP
            )
        else:
            InfoBar.success(
                title="分析完成",
                content=f"共分析 {len(trace_results)} 条数据，全部 {matched_count} 项均已成功在源文件夹中匹配！",
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

"""
Enhancer Workflow Page (Tab 2)
Implements 'Aiarty Image Enhancer（画质增强）':
- Module 1: Image filtering based on [逻辑父文件夹名]__[纯数字序号].png
- Transition Bar: "准备复制到[逻辑父文件夹]" Action Button
- Module 2: Identical to Matting Module 2 (Trace & Copy to matching parent folders)
"""
import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QThreadPool, QRunnable, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame
)
from qfluentwidgets import (
    SmoothScrollArea, CardWidget, TitleLabel, CaptionLabel,
    PrimaryPushButton, FluentIcon, InfoBar, InfoBarPosition, isDarkTheme
)

from src.config import ALL_IMAGE_EXTENSIONS, EnhancerImageItem, match_enhancer_image
from src.ui.module1.folder_drop_zone import FolderDropZoneWidget
from src.ui.pages.enhancer_result_table import EnhancerResultTableWidget
from src.ui.module2.module2_widget import Module2Widget


class EnhancerScannerSignals(QObject):
    progress = Signal(int, int, str)
    finished = Signal(list)
    error = Signal(str)


class EnhancerScannerWorker(QRunnable):
    """画质增强模块专属后台图片扫描线程"""
    def __init__(self, folder_paths: List[Path], recursive: bool = True):
        super().__init__()
        self.folder_paths = folder_paths
        self.recursive = recursive
        self.signals = EnhancerScannerSignals()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        results: List[EnhancerImageItem] = []
        total_folders = len(self.folder_paths)

        try:
            for f_idx, folder in enumerate(self.folder_paths, start=1):
                if self._is_cancelled:
                    break

                self.signals.progress.emit(f_idx, total_folders, folder.name)

                if not folder.is_dir():
                    continue

                folder_root_name = folder.name

                if self.recursive:
                    for root, _, files in os.walk(folder):
                        if self._is_cancelled:
                            break
                        cur_path = Path(root)
                        rel_parts = cur_path.relative_to(folder.parent).parts
                        display_name = "\\".join(rel_parts) if rel_parts else folder_root_name

                        for filename in sorted(files):
                            ext = Path(filename).suffix.lower()
                            if ext in ALL_IMAGE_EXTENSIONS:
                                file_path = cur_path / filename
                                is_valid, logical_parent, seq, reason = match_enhancer_image(filename)
                                results.append(EnhancerImageItem(
                                    file_path=file_path,
                                    folder_path=cur_path,
                                    folder_display_name=display_name,
                                    original_name=filename,
                                    is_valid=is_valid,
                                    logical_parent=logical_parent,
                                    sequence_num=seq,
                                    extension=ext,
                                    target_name=filename,
                                    status_message="有效" if is_valid else "无效",
                                    invalid_reason=reason
                                ))
                else:
                    for entry in sorted(folder.iterdir()):
                        if entry.is_file() and entry.suffix.lower() in ALL_IMAGE_EXTENSIONS:
                            is_valid, logical_parent, seq, reason = match_enhancer_image(entry.name)
                            results.append(EnhancerImageItem(
                                file_path=entry,
                                folder_path=folder,
                                folder_display_name=folder_root_name,
                                original_name=entry.name,
                                is_valid=is_valid,
                                logical_parent=logical_parent,
                                sequence_num=seq,
                                extension=entry.suffix.lower(),
                                target_name=entry.name,
                                status_message="有效" if is_valid else "无效",
                                invalid_reason=reason
                            ))

            self.signals.finished.emit(results)
        except Exception as e:
            self.signals.error.emit(str(e))


class EnhancerWorkflowPage(QWidget):
    """
    选项卡 2：Aiarty Image Enhancer（画质增强）
    包含：
    - 模块 1：画质增强图片识别（左侧子文件夹拖入区，右侧图片列表）
    - 衔接过渡栏：醒目按钮【准备复制到[逻辑父文件夹]】
    - 模块 2：溯源到父文件夹（与 Matting 模块 2 规则完全一致）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.current_worker = None

        self._init_ui()
        self._bind_events()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 平滑垂直滚动容器
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # 滚动容器内容部件
        self.content_widget = QWidget()
        self.content_widget.setObjectName("enhancerContentWidget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 12, 16)
        self.content_layout.setSpacing(16)

        # 区域 1：模块 1 复合卡片
        self.module_card = CardWidget(self.content_widget)
        card_layout = QVBoxLayout(self.module_card)
        card_layout.setContentsMargins(18, 16, 18, 18)
        card_layout.setSpacing(14)

        # 标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title = TitleLabel("模块 1：画质增强图片识别", self.module_card)
        self.title.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.desc = CaptionLabel("支持子文件夹拖拽筛选匹配 [逻辑父名]__[纯数字序号].png，区分有效与无效文件", self.module_card)
        header_layout.addWidget(self.desc)
        header_layout.addStretch()

        card_layout.addLayout(header_layout)

        # 左右两栏 Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.module_card)
        self.splitter.setHandleWidth(8)

        # 左侧：子文件夹拖入区
        self.left_drop_zone = FolderDropZoneWidget(self.splitter)
        self.left_drop_zone.setMinimumWidth(320)

        # 右侧：图片列表
        self.right_table = EnhancerResultTableWidget(self.splitter)
        self.right_table.setMinimumWidth(500)

        self.splitter.addWidget(self.left_drop_zone)
        self.splitter.addWidget(self.right_table)
        self.splitter.setSizes([360, 740])

        card_layout.addWidget(self.splitter, stretch=1)
        self.content_layout.addWidget(self.module_card)

        # 区域 2：模块 1 与 模块 2 之间的专属衔接过渡栏
        self.transition_bar = QFrame(self.content_widget)
        self.transition_bar.setObjectName("enhancerTransitionBar")
        transition_layout = QHBoxLayout(self.transition_bar)
        transition_layout.setContentsMargins(8, 12, 8, 12)
        transition_layout.setSpacing(20)

        left_line = QFrame(self.transition_bar)
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Sunken)
        transition_layout.addWidget(left_line, stretch=1)

        # 醒目的行动按钮：准备复制到[逻辑父文件夹]
        self.prepare_transfer_btn = PrimaryPushButton(
            FluentIcon.SAVE_COPY, "准备复制到[逻辑父文件夹]", self.transition_bar
        )
        self.prepare_transfer_btn.setFixedHeight(44)
        self.prepare_transfer_btn.setMinimumWidth(300)
        btn_font = self.prepare_transfer_btn.font()
        btn_font.setPointSize(11)
        btn_font.setBold(True)
        self.prepare_transfer_btn.setFont(btn_font)
        self.prepare_transfer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prepare_transfer_btn.clicked.connect(self._on_prepare_transfer_clicked)
        transition_layout.addWidget(self.prepare_transfer_btn)

        right_line = QFrame(self.transition_bar)
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Sunken)
        transition_layout.addWidget(right_line, stretch=1)

        self.content_layout.addWidget(self.transition_bar)

        # 区域 3：模块 2（溯源到父文件夹，初始半透明遮罩锁定）
        self.module2_widget = Module2Widget(self.content_widget)
        self.content_layout.addWidget(self.module2_widget)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

    def _bind_events(self):
        self.left_drop_zone.start_scan_requested.connect(self._start_scanning)
        self.left_drop_zone.folder_added.connect(self._on_folders_changed)
        self.left_drop_zone.folder_removed.connect(self._on_folders_changed)
        self.left_drop_zone.folders_cleared.connect(self._on_folders_changed)

    def _on_folders_changed(self, *args):
        """当模块1子文件夹变动时，右侧列表清空且模块2所有数据重置并重新半透明遮罩"""
        self.right_table.clear_results()
        self.module2_widget.reset_module()

    def _start_scanning(self, folder_paths: List[Path], recursive: bool = True):
        self.right_table.set_loading(True)
        self.right_table.status_info.setText("正在扫描图片...")

        worker = EnhancerScannerWorker(folder_paths, recursive=recursive)
        worker.signals.progress.connect(self._on_scan_progress)
        worker.signals.finished.connect(self._on_scan_finished)
        worker.signals.error.connect(self._on_scan_error)

        self.current_worker = worker
        self.thread_pool.start(worker)

    def _on_scan_progress(self, current: int, total: int, folder_name: str):
        self.right_table.status_info.setText(f"正在扫描 ({current}/{total}): {folder_name}")

    def _on_scan_finished(self, items: List[EnhancerImageItem]):
        self.right_table.set_loading(False)
        self.right_table.set_results(items)
        total = len(items)
        valid_count = sum(1 for it in items if it.is_valid)
        invalid_count = total - valid_count
        if total == 0:
            self.right_table.status_info.setText("扫描完成：文件夹内未发现图片文件")
        elif valid_count == 0:
            self.right_table.status_info.setText(f"扫描完成：共 {total} 张图片，均不符合规则（全部为无效）")
        else:
            self.right_table.status_info.setText(
                f"扫描完成：共 {total} 张图片（有效 {valid_count} 张，无效 {invalid_count} 张）"
            )

    def _on_scan_error(self, err_msg: str):
        self.right_table.set_loading(False)
        self.right_table.status_info.setText(f"扫描发生错误: {err_msg}")

    def _on_prepare_transfer_clicked(self):
        """
        点击「准备复制到[逻辑父文件夹]」校验逻辑：
        - 如果模块1扫描出的图片列表中，有有效图片，则解锁模块2并注入数据源；
        - 如果模块1扫描出的图片列表中，无有效图片，则飘字提示：“抱歉，没有有效图片可以转移”
        """
        valid_items = [it for it in self.right_table.image_items if it.is_valid]

        if not valid_items:
            InfoBar.warning(
                title="无法转移",
                content="抱歉，没有有效图片可以转移",
                parent=self.window(),
                duration=3500,
                position=InfoBarPosition.TOP
            )
            self.module2_widget.set_locked(True)
        else:
            self.module2_widget.set_source_items(valid_items)
            self.module2_widget.set_locked(False)
            InfoBar.success(
                title="已就绪",
                content=f"已成功捕获 {len(valid_items)} 张「有效」图片，模块 2 已成功解锁！",
                parent=self.window(),
                duration=3000,
                position=InfoBarPosition.TOP
            )
            self.scroll_area.ensureWidgetVisible(self.module2_widget)

    def reset_page(self):
        """重置画质增强工作流页面为初始状态"""
        if self.current_worker and hasattr(self.current_worker, 'cancel'):
            self.current_worker.cancel()
            self.current_worker = None

        self.left_drop_zone.clear_all()
        self.left_drop_zone.recursive_checkbox.setChecked(True)
        self.right_table.clear_results()
        self.right_table.only_valid_checkbox.setChecked(False)
        self.right_table.status_info.setText("就绪")
        self.right_table.set_loading(False)
        self.module2_widget.reset_module()
        self.scroll_area.verticalScrollBar().setValue(0)

    def update_theme(self, is_dark: bool):
        if is_dark:
            self.desc.setStyleSheet("color: rgba(255, 255, 255, 0.65); margin-top: 4px;")
        else:
            self.desc.setStyleSheet("color: rgba(0, 0, 0, 0.55); margin-top: 4px;")

        self.left_drop_zone.update_theme(is_dark)
        self.right_table.update_theme(is_dark)
        self.module2_widget.update_theme(is_dark)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        viewport_height = self.scroll_area.viewport().height()
        if viewport_height > 200:
            self.module_card.setMinimumHeight(max(520, viewport_height - 90))

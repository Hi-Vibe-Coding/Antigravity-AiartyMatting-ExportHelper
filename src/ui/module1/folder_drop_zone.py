"""
Folder Drop Zone (Module 1 Left Box)
Accepts drag-and-drop of subfolders, prevents duplicates, displays folder cards with icons,
and provides '开始扫描' button at the bottom right.
"""
from pathlib import Path
from typing import List, Set

from PySide6.QtCore import Qt, Signal, QFileInfo
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QFileDialog, QSizePolicy
)
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton, TransparentToolButton,
    FluentIcon, IconWidget, InfoBar, InfoBarPosition, SmoothScrollArea, StrongBodyLabel,
    CaptionLabel, SubtitleLabel
)


class FolderItemCard(CardWidget):
    """单条已添加文件夹的卡片项"""
    removed = Signal(Path)

    def __init__(self, folder_path: Path, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.setFixedHeight(48)
        self.setToolTip(str(folder_path))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(10)

        # 文件夹图标
        self.icon_widget = IconWidget(FluentIcon.FOLDER, self)
        self.icon_widget.setFixedSize(20, 20)
        layout.addWidget(self.icon_widget)

        # 文件夹名称
        self.name_label = StrongBodyLabel(folder_path.name)
        self.name_label.setStyleSheet("font-weight: 500;")
        layout.addWidget(self.name_label, stretch=1)

        # 删除按钮
        self.delete_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.delete_btn.setToolTip("从列表中移除")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.clicked.connect(lambda: self.removed.emit(self.folder_path))
        layout.addWidget(self.delete_btn)


class DropContainer(QFrame):
    """支持拖拽子文件夹的专用容器"""
    folder_dropped = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropContainer")
        self.setStyleSheet("""
            QFrame#dropContainer {
                border: 2px dashed rgba(120, 120, 120, 0.35);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.03);
            }
            QFrame#dropContainer:hover {
                border: 2px dashed #0078d4;
                background-color: rgba(0, 120, 212, 0.05);
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # 检查是否有文件夹
            has_dir = False
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if QFileInfo(local_path).isDir():
                    has_dir = True
                    break
            if has_dir:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path and QFileInfo(local_path).isDir():
                self.folder_dropped.emit(Path(local_path))
        event.acceptProposedAction()


class FolderDropZoneWidget(QFrame):
    """
    区域1左侧模块：子文件夹拖拽与管理面板
    """
    start_scan_requested = Signal(list)  # 传递 List[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_set: Set[Path] = set()
        self.folder_list: List[Path] = []

        self._init_ui()

    def _init_ui(self):
        self.setObjectName("folderDropZoneWidget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 头部标题与数量标签
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.title_label = SubtitleLabel("子文件夹拖入区")
        header_layout.addWidget(self.title_label)

        self.count_badge = CaptionLabel("(0 个目录)")
        self.count_badge.setStyleSheet("color: rgba(128, 128, 128, 0.9); font-weight: 500;")
        header_layout.addWidget(self.count_badge)

        header_layout.addStretch()

        # 辅助手动添加按钮
        self.add_btn = PushButton(FluentIcon.ADD, "浏览添加", self)
        self.add_btn.setFixedHeight(30)
        self.add_btn.clicked.connect(self._choose_folder_dialog)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # 中部拖拽与列表展示区域
        self.drop_container = DropContainer(self)
        drop_layout = QVBoxLayout(self.drop_container)
        drop_layout.setContentsMargins(8, 8, 8, 8)
        drop_layout.setSpacing(6)

        # 拖拽空状态提示占位
        self.placeholder_widget = QWidget(self.drop_container)
        placeholder_layout = QVBoxLayout(self.placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.setSpacing(10)

        placeholder_icon = IconWidget(FluentIcon.FOLDER_ADD, self.placeholder_widget)
        placeholder_icon.setFixedSize(48, 48)
        placeholder_layout.addWidget(placeholder_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        placeholder_tip = StrongBodyLabel("拖拽子文件夹到此处")
        placeholder_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(placeholder_tip)

        placeholder_subtip = CaptionLabel("支持逐一拖入，系统将自动校验去重")
        placeholder_subtip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_subtip.setStyleSheet("color: rgba(128, 128, 128, 0.8);")
        placeholder_layout.addWidget(placeholder_subtip)

        drop_layout.addWidget(self.placeholder_widget)

        # 滚动列表区域（当有文件夹时展示）
        self.scroll_area = SmoothScrollArea(self.drop_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_content_widget = QWidget()
        self.list_content_layout = QVBoxLayout(self.list_content_widget)
        self.list_content_layout.setContentsMargins(4, 4, 4, 4)
        self.list_content_layout.setSpacing(8)
        self.list_content_layout.addStretch()

        self.scroll_area.setWidget(self.list_content_widget)
        self.scroll_area.hide()
        drop_layout.addWidget(self.scroll_area)

        layout.addWidget(self.drop_container, stretch=1)

        # 底部操作栏（包含右下角的“开始扫描”按钮）
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.clear_btn = PushButton(FluentIcon.DELETE, "清空列表", self)
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.hide()
        bottom_layout.addWidget(self.clear_btn)

        bottom_layout.addStretch()

        # 关键需求：拖拽完成后，在右下角出现按钮“开始扫描”
        self.scan_btn = PrimaryPushButton(FluentIcon.SEARCH, "开始扫描", self)
        self.scan_btn.setFixedHeight(34)
        self.scan_btn.setFixedWidth(120)
        self.scan_btn.clicked.connect(self._on_start_scan_clicked)
        self.scan_btn.hide()  # 初始没有文件夹时隐藏
        bottom_layout.addWidget(self.scan_btn)

        layout.addLayout(bottom_layout)

        # 绑定拖拽事件
        self.drop_container.folder_dropped.connect(self.add_folder)

    def _choose_folder_dialog(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择要添加的子文件夹")
        if dir_path:
            self.add_folder(Path(dir_path))

    def add_folder(self, folder_path: Path):
        folder_path = folder_path.resolve()
        if not folder_path.is_dir():
            InfoBar.warning(
                title="无效目标",
                content=f"'{folder_path.name}' 不是一个文件夹，仅支持拖拽子文件夹！",
                parent=self.window(),
                duration=2500,
                position=InfoBarPosition.TOP
            )
            return

        if folder_path in self.folder_set:
            InfoBar.info(
                title="重复文件夹",
                content=f"文件夹 '{folder_path.name}' 已存在列表中，已自动忽略重复项。",
                parent=self.window(),
                duration=2000,
                position=InfoBarPosition.TOP
            )
            return

        # 添加到集合与列表
        self.folder_set.add(folder_path)
        self.folder_list.append(folder_path)

        # 创建卡片
        card = FolderItemCard(folder_path, self.list_content_widget)
        card.removed.connect(self.remove_folder)
        # 插入到底部弹簧之前
        self.list_content_layout.insertWidget(self.list_content_layout.count() - 1, card)

        self._update_state()

    def remove_folder(self, folder_path: Path):
        if folder_path in self.folder_set:
            self.folder_set.remove(folder_path)
            self.folder_list.remove(folder_path)

            # 移除 UI 卡片
            for i in range(self.list_content_layout.count() - 1):
                item = self.list_content_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), FolderItemCard):
                    if item.widget().folder_path == folder_path:
                        w = item.widget()
                        self.list_content_layout.removeWidget(w)
                        w.deleteLater()
                        break

            self._update_state()

    def clear_all(self):
        self.folder_set.clear()
        self.folder_list.clear()

        # 清除所有卡片
        while self.list_content_layout.count() > 1:
            item = self.list_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._update_state()

    def _update_state(self):
        count = len(self.folder_list)
        self.count_badge.setText(f"({count} 个目录)")

        has_items = count > 0
        self.placeholder_widget.setVisible(not has_items)
        self.scroll_area.setVisible(has_items)
        self.clear_btn.setVisible(has_items)
        # 右下角按钮“开始扫描”在有子文件夹时出现
        self.scan_btn.setVisible(has_items)

    def _on_start_scan_clicked(self):
        if not self.folder_list:
            InfoBar.warning(
                title="请先添加文件夹",
                content="请至少拖入一个子文件夹后再开始扫描。",
                parent=self.window(),
                duration=2000,
                position=InfoBarPosition.TOP
            )
            return
        self.start_scan_requested.emit(list(self.folder_list))

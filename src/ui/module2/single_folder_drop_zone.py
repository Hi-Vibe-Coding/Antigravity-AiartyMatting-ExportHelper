"""
Single Folder Drop Zone Widget (Module 2 Left Box)
Accepts exactly ONE target root/parent folder via drag-and-drop or browsing.
Allows clearing and re-dragging.
Provides '开始分析' button at bottom-right.
"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QFileInfo, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QFileDialog
)
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton, TransparentToolButton,
    FluentIcon, IconWidget, InfoBar, InfoBarPosition, StrongBodyLabel,
    CaptionLabel, SubtitleLabel, RoundMenu, Action, isDarkTheme
)

from src.ui.clipboard_helper import extract_folders_from_clipboard


class SingleFolderCard(CardWidget):
    """展示已选择的单个目标父文件夹"""
    cleared = Signal()

    def __init__(self, folder_path: Path, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.setFixedHeight(54)
        self.setToolTip(str(folder_path))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 10, 8)
        layout.setSpacing(12)

        self.icon_widget = IconWidget(FluentIcon.FOLDER, self)
        self.icon_widget.setFixedSize(24, 24)
        layout.addWidget(self.icon_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.name_label = StrongBodyLabel(folder_path.name, self)
        font = self.name_label.font()
        font.setWeight(QFont.Weight.DemiBold)
        self.name_label.setFont(font)
        text_layout.addWidget(self.name_label)

        self.path_label = CaptionLabel(str(folder_path), self)
        self.path_label.setStyleSheet("color: rgba(140, 140, 140, 0.9);")
        text_layout.addWidget(self.path_label)

        layout.addLayout(text_layout, stretch=1)

        # 清空/移除按钮
        self.clear_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.clear_btn.setToolTip("清空此文件夹，重新拖拽")
        self.clear_btn.setFixedSize(30, 30)
        self.clear_btn.clicked.connect(self.cleared.emit)
        layout.addWidget(self.clear_btn)


class SingleFolderDropContainer(QFrame):
    """支持拖拽单个文件夹的放置区域"""
    folder_dropped = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("singleFolderDropContainer")
        self.update_style(isDarkTheme())

    def update_style(self, is_dark: bool):
        if is_dark:
            self.setStyleSheet("""
                QFrame#singleFolderDropContainer {
                    border: 2px dashed rgba(255, 255, 255, 0.25);
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.04);
                }
                QFrame#singleFolderDropContainer:hover {
                    border: 2px dashed #0078d4;
                    background-color: rgba(0, 120, 212, 0.15);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#singleFolderDropContainer {
                    border: 2px dashed rgba(0, 0, 0, 0.20);
                    border-radius: 8px;
                    background-color: rgba(0, 0, 0, 0.02);
                }
                QFrame#singleFolderDropContainer:hover {
                    border: 2px dashed #0078d4;
                    background-color: rgba(0, 120, 212, 0.06);
                }
            """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            try:
                for url in event.mimeData().urls():
                    local_path = url.toLocalFile()
                    if local_path and QFileInfo(local_path).isDir():
                        event.acceptProposedAction()
                        return
            except Exception:
                pass
        event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        try:
            if event.mimeData().hasUrls():
                dirs = []
                for url in event.mimeData().urls():
                    local_path = url.toLocalFile()
                    if local_path and QFileInfo(local_path).isDir():
                        dirs.append(Path(local_path))
                if dirs:
                    # 严格限制：只接收一个文件夹（若拖入多个，取首个有效文件夹）
                    self.folder_dropped.emit(dirs[0])
                    event.acceptProposedAction()
                    return
        except Exception:
            pass
        event.ignore()


class SingleFolderDropZone(QWidget):
    """
    模块2左侧：目标父文件夹拖拽接收区
    - 拖拽目标父文件夹到此处（只能设置一个）
    - 可以清空，重新拖拽
    - 右下角配备“开始分析”按钮
    """
    start_analyze_requested = Signal(Path)  # 触发“开始分析”信号，传出目标父文件夹
    folder_selected = Signal(Path)          # 当拖入/选择新源文件夹时发出信号
    folder_cleared = Signal()               # 当移除/清空源文件夹时发出信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_folder: Optional[Path] = None

        self._init_ui()
        self._bind_events()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 顶部标题栏
        top_layout = QHBoxLayout()
        self.header_title = SubtitleLabel("源文件夹", self)
        self.header_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        top_layout.addWidget(self.header_title)

        top_layout.addStretch()

        self.clear_btn = PushButton(FluentIcon.DELETE, "清空", self)
        self.clear_btn.setFixedHeight(28)
        self.clear_btn.setEnabled(False)
        top_layout.addWidget(self.clear_btn)

        layout.addLayout(top_layout)

        # 拖拽接收放置容器
        self.drop_container = SingleFolderDropContainer(self)
        drop_layout = QVBoxLayout(self.drop_container)
        drop_layout.setContentsMargins(16, 20, 16, 20)
        drop_layout.setSpacing(10)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 未选择文件夹时的引导状态
        self.empty_widget = QWidget(self.drop_container)
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(8)

        self.drop_icon = IconWidget(FluentIcon.FOLDER_ADD, self.empty_widget)
        self.drop_icon.setFixedSize(48, 48)
        empty_layout.addWidget(self.drop_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.tip_label = StrongBodyLabel("拖拽目标父文件夹到此处", self.empty_widget)
        self.tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.tip_label)

        self.sub_tip = CaptionLabel("仅限单个目标根文件夹（支持拖拽或右键粘贴）", self.empty_widget)
        self.sub_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.sub_tip)

        self.browse_btn = PushButton(FluentIcon.FOLDER, "浏览选择文件夹", self.empty_widget)
        self.browse_btn.setFixedHeight(30)
        empty_layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        drop_layout.addWidget(self.empty_widget)

        # 已选择文件夹时的卡片展示状态
        self.card_container = QWidget(self.drop_container)
        card_layout = QVBoxLayout(self.card_container)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folder_card: Optional[SingleFolderCard] = None
        self.card_container.hide()

        drop_layout.addWidget(self.card_container)

        layout.addWidget(self.drop_container, stretch=1)

        # 底部操作栏：右下角“开始分析”按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.analyze_btn = PrimaryPushButton(FluentIcon.SEARCH, "开始分析", self)
        self.analyze_btn.setFixedHeight(34)
        self.analyze_btn.setEnabled(False)
        bottom_layout.addWidget(self.analyze_btn)

        layout.addLayout(bottom_layout)

    def _bind_events(self):
        self.drop_container.folder_dropped.connect(self.set_folder)

        # 为拖拽容器及内部所有子部件统一安装事件过滤器（右键弹出菜单）
        self._install_paste_filter(self.drop_container)

        self.browse_btn.clicked.connect(self._on_browse_clicked)
        self.clear_btn.clicked.connect(self.clear_folder)
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)

    def _install_paste_filter(self, widget: QWidget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                self._show_context_menu(QCursor.pos(), is_global=True)
                return True
        elif event.type() == QEvent.Type.ContextMenu:
            self._show_context_menu(QCursor.pos(), is_global=True)
            return True
        return super().eventFilter(watched, event)

    def _show_context_menu(self, pos, is_global: bool = False):
        menu = RoundMenu(parent=self)
        paste_act = Action(FluentIcon.PASTE, "粘贴文件夹", self)
        paste_act.triggered.connect(self.paste_from_clipboard)
        menu.addAction(paste_act)
        global_pos = pos if is_global else self.drop_container.mapToGlobal(pos)
        menu.exec(global_pos)

    def paste_from_clipboard(self):
        """响应粘贴操作：从剪贴板提取目标父文件夹并设置"""
        folders = extract_folders_from_clipboard()
        if not folders:
            InfoBar.warning(
                title="未检测到文件夹",
                content="剪贴板中未检测到有效文件夹路径，请先在资源管理器中复制目标文件夹或其完整路径！",
                parent=self.window(),
                duration=2500,
                position=InfoBarPosition.TOP
            )
            return

        target_folder = folders[0]
        self.set_folder(target_folder)

        if len(folders) > 1:
            InfoBar.info(
                title="已设置首个文件夹",
                content=f"检测到剪贴板包含多个文件夹，已将首个文件夹 '{target_folder.name}' 设为源文件夹。",
                parent=self.window(),
                duration=3000,
                position=InfoBarPosition.TOP
            )
        else:
            InfoBar.success(
                title="粘贴成功",
                content=f"已成功将 '{target_folder.name}' 设为目标源文件夹！",
                parent=self.window(),
                duration=2000,
                position=InfoBarPosition.TOP
            )

    def _on_browse_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "选择模块2源文件夹（目标父文件夹）")
        if folder:
            self.set_folder(Path(folder))

    def set_folder(self, folder_path: Path):
        """设置选中的源文件夹，并更新界面"""
        if not folder_path.is_dir():
            return

        self.selected_folder = folder_path

        # 移除旧卡片
        if self.folder_card:
            self.folder_card.deleteLater()
            self.folder_card = None

        self.folder_card = SingleFolderCard(folder_path, self.card_container)
        self.folder_card.cleared.connect(self.clear_folder)
        self._install_paste_filter(self.folder_card)
        self.card_container.layout().addWidget(self.folder_card)

        self.empty_widget.hide()
        self.card_container.show()
        self.clear_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.folder_selected.emit(folder_path)

    def clear_folder(self):
        """清空已选文件夹，允许重新拖拽"""
        self.selected_folder = None
        if self.folder_card:
            self.folder_card.deleteLater()
            self.folder_card = None

        self.card_container.hide()
        self.empty_widget.show()
        self.clear_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.folder_cleared.emit()

    def _on_analyze_clicked(self):
        if self.selected_folder:
            self.start_analyze_requested.emit(self.selected_folder)

    def update_theme(self, is_dark: bool):
        self.drop_container.update_style(is_dark)
        if is_dark:
            self.sub_tip.setStyleSheet("color: rgba(255, 255, 255, 0.60);")
        else:
            self.sub_tip.setStyleSheet("color: rgba(0, 0, 0, 0.55);")

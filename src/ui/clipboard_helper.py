"""
Clipboard Folder Extraction Utilities.
Supports:
1. Windows Explorer copy (CF_HDROP / text/uri-list) via mimeData.urls()
2. Plain text folder path strings (single or multi-line, with or without quotes) via mimeData.text()
"""
from pathlib import Path
from typing import List

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFileInfo


def extract_folders_from_clipboard() -> List[Path]:
    """
    从系统剪贴板中提取所有有效的本地文件夹路径列表（自动解析绝对路径、去重并保持原有顺序）
    """
    clipboard = QApplication.clipboard()
    if not clipboard:
        return []

    mime_data = clipboard.mimeData()
    if not mime_data:
        return []

    folders: List[Path] = []
    seen = set()

    def _add_if_dir(path_obj: Path):
        try:
            resolved = path_obj.resolve()
            if resolved.is_dir() and resolved not in seen:
                seen.add(resolved)
                folders.append(resolved)
        except Exception:
            pass

    # 1. 优先读取 URLs (Windows 资源管理器中 Ctrl+C 复制的文件夹)
    if mime_data.hasUrls():
        for url in mime_data.urls():
            local_path = url.toLocalFile()
            if local_path and QFileInfo(local_path).isDir():
                _add_if_dir(Path(local_path))

    # 2. 若未从 URLs 解析到文件夹，尝试从 Text 中提取 (从地址栏或文本编辑器中复制的路径)
    if not folders and mime_data.hasText():
        raw_text = mime_data.text().strip()
        for line in raw_text.splitlines():
            clean = line.strip().strip('"').strip("'")
            if clean and QFileInfo(clean).isDir():
                _add_if_dir(Path(clean))

    return folders

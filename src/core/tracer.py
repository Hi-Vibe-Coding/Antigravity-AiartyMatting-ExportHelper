"""
Module 2 Data Models
Defines data structures for '溯源到父文件夹' analysis.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


def format_relative_path(path: Path, max_levels: int) -> str:
    """
    格式化路径，尽可能显示后 max_levels 层名称（Windows 斜杠拼接）
    例：
      path='D:/Aiarty Image-测试用例/Batch_Export_案例3/B0-001__1.png', max_levels=3
      -> 'Aiarty Image-测试用例\\Batch_Export_案例3\\B0-001__1.png'
      path='D:/A 预制/Bracelet/B0-001', max_levels=3
      -> 'A 预制\\Bracelet\\B0-001'
    """
    resolved = path.resolve()
    parts = []
    for part in resolved.parts:
        clean = part.replace('\\', '').replace('/', '')
        if clean:
            parts.append(clean)
    take = parts[-max_levels:] if len(parts) >= max_levels else parts
    return "\\".join(take)


@dataclass
class LogicalTraceItem:
    """
    模块2对照数据项：
    - 字段1: 序号 (original_item_idx)
    - 字段2: 原文件 (raw_file_display: 纯文件名，如: B0-001__1_attr1_subject.png)
    - 字段3: 预期重命名 (expected_rename: 如 B0-001__1.png)
    - 字段4: 状态 (status_display: 错误状态 或 即将被写入到XXXX 或 同名文件将覆盖!)
    """
    original_item_idx: int                          # 对应模块1的序号索引
    raw_file_display: str                           # 原文件相对路径（含上层文件夹与文件名）
    expected_rename: str                            # 预期重命名 (原 target_name)
    logical_parent: str                             # 逻辑父文件夹名 (如 B0-001)
    status_display: str                             # 状态文本
    status_type: str = "error"                      # "normal" | "override" | "error"
    full_source_file: Optional[Path] = None         # 原文件完整物理路径
    matched_target_folder: Optional[Path] = None   # 匹配到的目标父文件夹
    dest_file_path: Optional[Path] = None           # 目标文件完整物理路径
    dest_folder_display: str = ""                   # 目标文件夹相对显示路径（如 A 预制\Bracelet\B0-001）
    candidate_folders: Optional[List[Path]] = None  # 候选文件夹列表（同名不唯一时）
    existing_same_stem_files: Optional[List[Path]] = None  # 目标文件夹中已存在的同名图片文件列表 (如 B0-001_1.jpg, B0-001_1.png)
    is_copied: bool = False                         # 是否已经成功执行过复制操作

    def __post_init__(self):
        if self.existing_same_stem_files is None:
            self.existing_same_stem_files = []


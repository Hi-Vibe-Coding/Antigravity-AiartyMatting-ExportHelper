"""
Module 2 Data Models
Defines data structures for '溯源到父文件夹' analysis.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LogicalTraceItem:
    """
    模块2专属数据项：
    - 记录模块1中每条图片数据的逻辑父文件夹
    - 记录原文件名及目标重命名
    - 记录在模块2源文件夹中的溯源命中结果与状态
    """
    original_item_idx: int                 # 对应模块1的序号索引
    original_name: str                     # 原文件名
    target_name: str                       # 目标重命名
    logical_parent: str                    # 逻辑父文件夹名 (如 B0-001)
    matched_target_folder: Optional[Path] = None  # 在模块2源文件夹中找到的目标同名文件夹路径
    status: str = "无法找到"                # "已匹配" | "无法找到"
    is_matched: bool = False               # 是否成功匹配到父文件夹

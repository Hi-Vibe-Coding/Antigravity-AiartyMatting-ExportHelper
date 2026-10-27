"""
Application configuration and global constants.
"""
from dataclasses import dataclass
from pathlib import Path
import re

APP_NAME_EN = "Antigravity-AiartyMatting-ExportHelper"
APP_NAME_CN = "AiartyMatting 导出助手"
APP_VERSION = "1.0.0"

# 支持的图片扩展名（小写）
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# 默认的匹配后缀（特殊机制）
DEFAULT_SPECIAL_SUFFIX = "_attr1_subject"

# 正则表达式：用于提取逻辑父文件夹名称
# 例如：AAA_attr1_subject.png -> 逻辑父名称为 AAA, 扩展名为 .png
def build_pattern(suffix: str = DEFAULT_SPECIAL_SUFFIX) -> re.Pattern:
    escaped_suffix = re.escape(suffix)
    ext_pattern = r"\.(png|jpg|jpeg|webp)"
    return re.compile(rf"^(?P<logical_parent>.+){escaped_suffix}(?P<ext>{ext_pattern})$", re.IGNORECASE)

DEFAULT_IMAGE_PATTERN = build_pattern(DEFAULT_SPECIAL_SUFFIX)


@dataclass
class MatchedImageItem:
    """被识别出的有效图片数据结构"""
    file_path: Path
    folder_path: Path
    original_name: str
    logical_parent: str
    extension: str
    target_name: str
    is_renamed: bool = False
    status_message: str = "待处理"

"""
Application configuration and global constants.
"""
from dataclasses import dataclass
from pathlib import Path
import re

APP_NAME_EN = "Antigravity-AiartyMatting-ExportHelper"
APP_NAME_CN = "AiartyMatting 导出助手"
APP_VERSION = "1.0.0"

# 扫描识别的所有图片格式集合
ALL_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# 默认的匹配后缀（特殊机制）
DEFAULT_SPECIAL_SUFFIX = "_attr1_subject"

# 新命名规则正则说明：
# 1. 扩展名必须为 .png (大小写不敏感)
# 2. 尾部必须是 _attr1_subject
# 3. 紧邻是纯数字文本组合: (?P<seq>\d+)
# 4. 连续2个下划线: __
# 5. 逻辑父文件夹名: [字母+纯数字]-[纯数字]
IMAGE_PATTERN = re.compile(
    r"^(?P<logical_parent>(?P<left_code>[a-zA-Z]+\d+)-(?P<right_code>\d+))__(?P<seq>\d+)_attr1_subject(?P<ext>\.png)$",
    re.IGNORECASE
)


@dataclass
class MatchedImageItem:
    """扫描到的所有图片数据结构（区分有效与无效状态）"""
    file_path: Path
    folder_path: Path             # 实际所在物理路径（用于重命名更名操作）
    folder_display_name: str = "" # 向上计算的展示路径（如 Batch_Export_案例3\新建文件夹）
    original_name: str = ""
    is_valid: bool = False
    logical_parent: str = "-"
    sequence_num: str = "-"
    extension: str = ""
    target_name: str = "-"
    is_renamed: bool = False
    status_message: str = "无效"  # "待重命名" | "无效" | "重命名成功" | "重命名失败: ..."
    invalid_reason: str = ""     # 无效的具体原因说明

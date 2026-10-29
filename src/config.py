"""
Application configuration and global constants.
"""
from dataclasses import dataclass
from pathlib import Path
import re

APP_NAME_EN = "Aiarty-Image-ExportHelper"
APP_NAME_CN = "Aiarty Image 导出助手"
APP_VERSION = "1.0.1"

# 扫描识别的所有图片格式集合
ALL_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# 默认的匹配后缀（特殊机制）
DEFAULT_SPECIAL_SUFFIX = "_attr1_subject"

# Matting（抠图）命名规则正则说明：
# 1. 扩展名必须为 .png (大小写不敏感)
# 2. 尾部必须是 _attr1_subject
# 3. 紧邻是纯数字文本组合: (?P<seq>\d+)
# 4. 连续2个下划线: __
# 5. 逻辑父文件夹名: [字母+纯数字]-[纯数字]
IMAGE_PATTERN = re.compile(
    r"^(?P<logical_parent>(?P<left_code>[a-zA-Z]+\d+)-(?P<right_code>\d+))__(?P<seq>\d+)_attr1_subject(?P<ext>\.png)$",
    re.IGNORECASE
)

# Enhancer（画质增强）筛选规则正则说明：
# 格式：[逻辑父文件夹名]__[纯数字序号].png
# 1. 扩展名必须为 .png (大小写不敏感)
# 2. 必须紧接纯数字组合 (?P<seq>\d+)
# 3. 必须通过连续双下划线 '__' 分隔
# 4. 逻辑父文件夹名: [字母+纯数字]-[纯数字]
#    - 左侧: 26个英文字母在前，紧跟纯数字 (如 B0, ABc00)
#    - 中间: 连字符 '-'
#    - 右侧: 纯数字 (如 001, 101)
ENHANCER_IMAGE_PATTERN = re.compile(
    r"^(?P<logical_parent>(?P<left_code>[a-zA-Z]+\d+)-(?P<right_code>\d+))__(?P<seq>\d+)(?P<ext>\.png)$",
    re.IGNORECASE
)


def match_enhancer_image(filename: str):
    """
    针对 Enhancer 筛选规则验证文件名并提取逻辑元数据
    返回: (is_valid: bool, logical_parent: str, seq: str, invalid_reason: str)
    """
    m = ENHANCER_IMAGE_PATTERN.match(filename)
    if m:
        return True, m.group("logical_parent"), m.group("seq"), ""

    ext = Path(filename).suffix.lower()
    if ext != ".png":
        return False, "-", "-", f"扩展名必须为 .png（当前为 '{ext}'）"

    stem = Path(filename).stem
    if "__" not in stem:
        return False, "-", "-", "缺少双下划线 '__' 分隔符"

    parts = stem.split("__")
    if len(parts) != 2:
        return False, "-", "-", "文件名只能包含一组双下划线 '__' 分隔符"

    left, seq = parts[0], parts[1]
    if not seq.isdigit():
        return False, "-", "-", f"双下划线右侧序号必须为纯数字（当前为 '{seq}'）"

    if "-" not in left:
        return False, "-", "-", f"逻辑父名缺少连字符 '-'（当前为 '{left}'）"

    subparts = left.split("-")
    if len(subparts) != 2:
        return False, "-", "-", f"逻辑父名格式错误（当前为 '{left}'，应为 [字母+数字]-[数字]）"

    l_code, r_code = subparts[0], subparts[1]
    if not r_code.isdigit():
        return False, "-", "-", f"连字符右侧必须为纯数字（当前为 '{r_code}'，如 001、101）"

    if not re.match(r"^[a-zA-Z]+\d+$", l_code):
        return False, "-", "-", f"连字符左侧必须为英文字母在前紧跟纯数字（当前为 '{l_code}'，正确如 B0、ABc00）"

    return False, "-", "-", "未匹配规则 [逻辑父名]__[纯数字序号].png"


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


@dataclass
class EnhancerImageItem:
    """画质增强模块待扫描图片项数据结构"""
    file_path: Path
    folder_path: Path
    folder_display_name: str = ""
    original_name: str = ""
    is_valid: bool = False
    logical_parent: str = "-"
    sequence_num: str = "-"
    extension: str = ""
    target_name: str = ""
    status_message: str = "无效"  # "有效" | "无效"
    invalid_reason: str = ""

    def __post_init__(self):
        if not self.target_name and self.original_name:
            self.target_name = self.original_name

"""
Unit tests for the new special naming rule in Module 1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import IMAGE_PATTERN

test_cases = [
    # 正常有效图片
    ("B0-001__1_attr1_subject.png", True, "B0-001", "1", "B0-001__1.png"),
    ("ABc00-101__0123_attr1_subject.png", True, "ABc00-101", "0123", "ABc00-101__0123.png"),
    ("xyz99-000__1230_attr1_subject.PNG", True, "xyz99-000", "1230", "xyz99-000__1230.PNG"),
    ("A1-2__3_attr1_subject.png", True, "A1-2", "3", "A1-2__3.png"),

    # 无效格式与命名
    ("00ABc-001__1_attr1_subject.png", False, None, None, None),  # 数字在字母前
    ("0B-001__1_attr1_subject.png", False, None, None, None),     # 数字在字母前
    ("B-001__1_attr1_subject.png", False, None, None, None),      # 左侧无数字
    ("B0-abc__1_attr1_subject.png", False, None, None, None),     # 右侧非纯数字
    ("B0_001__1_attr1_subject.png", False, None, None, None),     # 缺少连字符 -
    ("B0-001_1_attr1_subject.png", False, None, None, None),      # 单下划线
    ("B0-001__abc_attr1_subject.png", False, None, None, None),   # 纯数字前非纯数字文本
    ("B0-001__1_attr1_subject.jpg", False, None, None, None),     # 非 png 格式
    ("B0-001__1_other_suffix.png", False, None, None, None),      # 后缀不匹配
]

def run_tests():
    for name, should_match, exp_parent, exp_seq, exp_target in test_cases:
        m = IMAGE_PATTERN.match(name)
        if should_match:
            assert m is not None, f"Failed to match valid file: {name}"
            assert m.group("logical_parent") == exp_parent, f"Parent error for {name}: {m.group('logical_parent')} != {exp_parent}"
            assert m.group("seq") == exp_seq, f"Seq error for {name}: {m.group('seq')} != {exp_seq}"
            target = f"{m.group('logical_parent')}__{m.group('seq')}{m.group('ext')}"
            assert target == exp_target, f"Target error for {name}: {target} != {exp_target}"
        else:
            assert m is None, f"Invalid file matched unexpectedly: {name}"

    print(f"All {len(test_cases)} new regex naming test cases passed successfully!")

if __name__ == "__main__":
    run_tests()

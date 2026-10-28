"""
Test Suite for Enhancer Filtering Rules:
Pattern: [逻辑父文件夹名]__[纯数字序号].png

Breakdown:
1. Extension must be .png (case-insensitive)
2. Followed immediately by digits: \d+
3. Separated by continuous double underscores '__'
4. Logical parent folder name: [letter+digits]-[digits]
   - Left side: 26 letters preceding digits (e.g. B0, ABc00; errors: 0B, 00ABc)
   - Hyphen '-'
   - Right side: pure digits (e.g. 001, 101)
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ENHANCER_IMAGE_PATTERN, match_enhancer_image


def test_enhancer_regex_and_matching():
    # 典型合法用例
    valid_cases = [
        ("B0-001__1.png", "B0-001", "1"),
        ("B0-001__0123.png", "B0-001", "0123"),
        ("ABc00-101__1.png", "ABc00-101", "1"),
        ("A1-2__3.png", "A1-2", "3"),
        ("Z99-9999__888.PNG", "Z99-9999", "888"),  # 大写扩展名
        ("AbCdEf123-45678__90.png", "AbCdEf123-45678", "90"),
    ]

    for fname, exp_parent, exp_seq in valid_cases:
        is_valid, parent, seq, reason = match_enhancer_image(fname)
        assert is_valid is True, f"Expected {fname} to be VALID, but got invalid: {reason}"
        assert parent == exp_parent, f"Expected parent {exp_parent}, got {parent}"
        assert seq == exp_seq, f"Expected seq {exp_seq}, got {seq}"
        assert reason == "", f"Expected empty reason for valid item, got {reason}"

    print(f"All {len(valid_cases)} valid cases passed [OK]")

    # 典型非法用例及原因检查
    invalid_cases = [
        # 1. 扩展名非 .png
        ("B0-001__1.jpg", "扩展名"),
        ("B0-001__1.jpeg", "扩展名"),
        ("B0-001__1.webp", "扩展名"),
        # 2. 序号非纯数字
        ("B0-001__abc.png", "纯数字"),
        ("B0-001__1a.png", "纯数字"),
        ("B0-001__.png", "纯数字"),
        # 3. 缺少或错误的双下划线
        ("B0-001_1.png", "__"),
        ("B0-001___1.png", ""),
        ("B0-001-1.png", "__"),
        # 4. 逻辑父名错误：左侧数字在字母前
        ("0B-001__1.png", "字母"),
        ("00ABc-001__1.png", "字母"),
        # 5. 逻辑父名错误：缺少数字
        ("B-001__1.png", "字母"),
        ("ABC-001__1.png", "字母"),
        # 6. 逻辑父名错误：右侧非纯数字
        ("B0-ABC__1.png", "纯数字"),
        ("B0-01a__1.png", "纯数字"),
        ("B0-__1.png", "纯数字"),
        # 7. 含有 Matting 的后缀 _attr1_subject
        ("B0-001__1_attr1_subject.png", ""),
    ]

    for fname, keyword in invalid_cases:
        is_valid, parent, seq, reason = match_enhancer_image(fname)
        assert is_valid is False, f"Expected {fname} to be INVALID, but got valid!"
        assert parent == "-", f"Expected parent '-' for invalid item, got {parent}"
        assert seq == "-", f"Expected seq '-' for invalid item, got {seq}"
        assert len(reason) > 0, f"Expected non-empty invalid reason for {fname}"
        if keyword:
            assert keyword in reason, f"Expected '{keyword}' in reason '{reason}' for {fname}"

    print(f"All {len(invalid_cases)} invalid cases passed [OK]")


if __name__ == "__main__":
    test_enhancer_regex_and_matching()
    print("\nALL ENHANCER RULE TESTS PASSED SUCCESSFULLY!")

"""
Unit test for target conflict detection (graying out rename button)
and '只显示有效' filter checkbox behavior.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.config import MatchedImageItem

def run_tests():
    app = QApplication(sys.argv)
    win = MainWindow()
    tbl = win.module1_widget.right_result_table

    # 1. 验证“只显示有效”复选框初始状态
    assert hasattr(tbl, "only_valid_checkbox"), "only_valid_checkbox must exist"
    assert tbl.only_valid_checkbox.isChecked() == False, "Default state must be unchecked"
    assert tbl.only_valid_checkbox.text() == "只显示有效"

    # 准备测试数据
    item_valid_1 = MatchedImageItem(
        file_path=Path("C:/test/F1/B0-001__1_attr1_subject.png"),
        folder_path=Path("C:/test/F1"),
        folder_display_name="F1",
        original_name="B0-001__1_attr1_subject.png",
        is_valid=True,
        logical_parent="B0-001",
        sequence_num="1",
        extension=".png",
        target_name="B0-001__1.png",
        is_renamed=False,
        status_message="待重命名"
    )

    item_valid_2 = MatchedImageItem(
        file_path=Path("C:/test/F1/B0-001__2_attr1_subject.png"),
        folder_path=Path("C:/test/F1"),
        folder_display_name="F1",
        original_name="B0-001__2_attr1_subject.png",
        is_valid=True,
        logical_parent="B0-001",
        sequence_num="2",
        extension=".png",
        target_name="B0-001__2.png",
        is_renamed=False,
        status_message="待重命名"
    )

    item_invalid = MatchedImageItem(
        file_path=Path("C:/test/F1/photo.jpg"),
        folder_path=Path("C:/test/F1"),
        folder_display_name="F1",
        original_name="photo.jpg",
        is_valid=False,
        logical_parent="-",
        sequence_num="-",
        extension=".jpg",
        target_name="-",
        is_renamed=False,
        status_message="无效",
        invalid_reason="格式非 .png"
    )

    # ---------------- 测试场景 1: 无冲突正常模式 ----------------
    tbl.set_results([item_valid_1, item_valid_2, item_invalid])

    # 默认不勾选：显示全部 3 条数据
    assert tbl.table.rowCount() == 3, f"Expected 3 rows, got {tbl.table.rowCount()}"
    # 无冲突：重命名按钮可用
    assert tbl.rename_btn.isEnabled() == True, "Rename button should be enabled"
    print("Normal mode (3 items, button enabled) [OK]")

    # 勾选“只显示有效”
    tbl.only_valid_checkbox.setChecked(True)
    # 过滤后：仅显示 2 条“待重命名”数据
    assert tbl.table.rowCount() == 2, f"Expected 2 rows when filtered, got {tbl.table.rowCount()}"
    for row in range(tbl.table.rowCount()):
        assert tbl.table.item(row, 5).text() == "待重命名"
    print("Only valid filtered mode (2 items, all 待重命名) [OK]")

    # 取消勾选：恢复显示 3 条
    tbl.only_valid_checkbox.setChecked(False)
    assert tbl.table.rowCount() == 3
    print("Uncheck restore mode [OK]")

    # ---------------- 测试场景 2: 出现重名冲突 ----------------
    # 模拟第 3 条数据与第 1 条数据指向相同的目标重命名 B0-001__1.png
    item_conflict = MatchedImageItem(
        file_path=Path("C:/test/F2/B0-001__1_attr1_subject.png"),
        folder_path=Path("C:/test/F2"),
        folder_display_name="F2",
        original_name="B0-001__1_attr1_subject.png",
        is_valid=True,
        logical_parent="B0-001",
        sequence_num="1",
        extension=".png",
        target_name="B0-001__1.png",  # 与 item_valid_1 重复！
        is_renamed=False,
        status_message="待重命名"
    )

    tbl.set_results([item_valid_1, item_valid_2, item_conflict, item_invalid])

    # 验证冲突检测：检测到目标名称重复
    assert "B0-001__1.png" in tbl.conflicting_targets
    # 验证核心需求：按钮必须为灰色不可用
    assert tbl.rename_btn.isEnabled() == False, "Rename button MUST BE DISABLED (grayed out) on conflict!"
    assert "冲突" in tbl.rename_btn.text()
    print("Conflict detection: rename button is grayed out [OK]")

    # 冲突情况下，勾选“只显示有效”：显示 3 条待重命名数据，且按钮依然保持灰色禁用
    tbl.only_valid_checkbox.setChecked(True)
    assert tbl.table.rowCount() == 3
    assert tbl.rename_btn.isEnabled() == False, "Rename button MUST REMAIN DISABLED when filtered on conflict!"
    print("Conflict detection under filter: rename button remains grayed out [OK]")

    print("All conflict detection and filter checkbox tests passed successfully!")

if __name__ == "__main__":
    run_tests()

"""
Test Suite for Module 2: '溯源到父文件夹'
Tests:
1. SingleFolderDropZone folder acceptance, clear, and analyze signal.
2. Matching logic in Module2Widget:
   - Finds matching directory -> status: '已匹配', is_matched: True
   - Directory does not exist -> status: '无法找到', is_matched: False
"""
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from src.config import MatchedImageItem
from src.ui.module2.module2_widget import Module2Widget


def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        root_dir = Path(temp_dir_str)
        # 在临时根目录下创建两个测试子目录：B0-001 和 C1-100
        target_b0_001 = root_dir / "B0-001"
        target_b0_001.mkdir()
        target_c1_100 = root_dir / "C1-100"
        target_c1_100.mkdir()

        # 初始化 Module2Widget
        m2 = Module2Widget()
        m2.set_locked(False)

        # 模拟模块1传递来的数据：
        # 项1: B0-001 (存在)
        # 项2: B0-001 (存在，同一父目录的另一张图)
        # 项3: D2-999 (不存在)
        # 项4: 无效项 (应当被过滤跳过)
        item1 = MatchedImageItem(
            file_path=Path("d:/1.png"), folder_path=Path("d:/"), original_name="B0-001__1_attr1_subject.png",
            is_valid=True, logical_parent="B0-001", sequence_num="1", extension=".png",
            target_name="B0-001__1.png", status_message="待重命名"
        )
        item2 = MatchedImageItem(
            file_path=Path("d:/2.png"), folder_path=Path("d:/"), original_name="B0-001__2_attr1_subject.png",
            is_valid=True, logical_parent="B0-001", sequence_num="2", extension=".png",
            target_name="B0-001__2.png", status_message="待重命名"
        )
        item3 = MatchedImageItem(
            file_path=Path("d:/3.png"), folder_path=Path("d:/"), original_name="D2-999__1_attr1_subject.png",
            is_valid=True, logical_parent="D2-999", sequence_num="1", extension=".png",
            target_name="D2-999__1.png", status_message="待重命名"
        )
        item_invalid = MatchedImageItem(
            file_path=Path("d:/invalid.png"), folder_path=Path("d:/"), original_name="invalid.png",
            is_valid=False, status_message="无效"
        )

        m2.set_source_items([item1, item2, item3, item_invalid])

        # 测试左侧拖拽/选择父文件夹容器
        m2.left_drop_zone.set_folder(root_dir)
        assert m2.left_drop_zone.selected_folder == root_dir, "Selected folder should match"
        assert m2.left_drop_zone.analyze_btn.isEnabled(), "Analyze button should be enabled"
        print("Folder selection and UI state [OK]")

        # 触发分析
        m2._run_analysis(root_dir)

        # 检查右侧表格分析结果
        results = m2.right_table.trace_items
        assert len(results) == 3, f"Expected 3 results (excluding invalid), got {len(results)}"

        # 验证第 1 项：B0-001 -> 已匹配
        assert results[0].logical_parent == "B0-001"
        assert results[0].is_matched == True
        assert results[0].status == "已匹配"
        assert results[0].matched_target_folder == target_b0_001
        print("Result 1 (B0-001 -> Matched) [OK]")

        # 验证第 2 项：B0-001 -> 已匹配
        assert results[1].logical_parent == "B0-001"
        assert results[1].is_matched == True
        assert results[1].status == "已匹配"
        print("Result 2 (B0-001 -> Matched) [OK]")

        # 验证第 3 项：D2-999 -> 无法找到
        assert results[2].logical_parent == "D2-999"
        assert results[2].is_matched == False
        assert results[2].status == "无法找到"
        assert results[2].matched_target_folder is None
        print("Result 3 (D2-999 -> Not Found) [OK]")

        # 验证表格行样式
        assert m2.right_table.table.rowCount() == 3
        status_cell_matched = m2.right_table.table.item(0, 4)
        status_cell_unmatched = m2.right_table.table.item(2, 4)
        assert status_cell_matched.text() == "已匹配"
        assert status_cell_unmatched.text() == "无法找到"
        print("Table row rendering and status text [OK]")

        # 测试清空并重新拖拽
        m2.left_drop_zone.clear_folder()
        assert m2.left_drop_zone.selected_folder is None
        assert not m2.left_drop_zone.analyze_btn.isEnabled()
        print("Clear and re-drag capability [OK]")

    print("\nALL MODULE 2 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()

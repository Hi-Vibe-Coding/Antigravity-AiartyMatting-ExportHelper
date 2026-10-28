"""
Test Suite for Module 2: Enhanced 4-column Table and Path Resolution
Verifies:
1. Field 1: 序号 (Index)
2. Field 2: 原文件 (raw_file_display: 尽可能2层文件夹+文件名, e.g. Aiarty Image-测试用例\\Batch_Export_案例3\\B0-001__1_attr1_subject.png)
3. Field 3: 预期重命名 (expected_rename, e.g. B0-001__1.png)
4. Field 4: 状态:
   - 无法找到 (Not found)
   - 同名文件夹不唯一 (Ambiguous)
   - 即将被写入到XXXX (Normal destination e.g. A 预制\\Bracelet\\B0-001)
   - 同名文件将覆盖! (File already exists at destination)
"""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from src.config import MatchedImageItem
from src.ui.module2.module2_widget import Module2Widget


def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        # 1. 构造测试源文件夹体系:
        # temp_dir / "RootFolder"
        #   ├── A_Prefab / Bracelet / B0-001  (目标同名目录1，为空目录 -> 状态应为 即将被写入到A_Prefab\Bracelet\B0-001)
        #   ├── A_Prefab / Rings / B0-002     (目标同名目录2，已有 B0-002__1.png -> 状态应为 同名文件将覆盖!)
        #   ├── Branch1 / C0-003              (同名目录3副本A)
        #   └── Branch2 / C0-003              (同名目录3副本B -> 状态应为 同名文件夹不唯一)
        root_folder = temp_dir / "RootFolder"
        b0_001_dir = root_folder / "A_Prefab" / "Bracelet" / "B0-001"
        b0_001_dir.mkdir(parents=True)

        b0_002_dir = root_folder / "A_Prefab" / "Rings" / "B0-002"
        b0_002_dir.mkdir(parents=True)
        # 在 B0-002 目录下提前创建一个同名文件以测试覆盖检测
        existing_file = b0_002_dir / "B0-002__1.png"
        existing_file.write_text("dummy image data")

        c0_003_dir1 = root_folder / "Branch1" / "C0-003"
        c0_003_dir1.mkdir(parents=True)
        c0_003_dir2 = root_folder / "Branch2" / "C0-003"
        c0_003_dir2.mkdir(parents=True)

        # 2. 构造模拟的原文件路径（多层结构测试）
        # d:/SomeProject/Aiarty_Images/Batch_Export_Case3/B0-001__1_attr1_subject.png
        src_file1 = temp_dir / "SomeProject" / "Aiarty_Images" / "Batch_Export_Case3" / "B0-001__1_attr1_subject.png"
        src_file1.parent.mkdir(parents=True)
        src_file1.write_text("image1")

        src_file2 = temp_dir / "SomeProject" / "Aiarty_Images" / "Batch_Export_Case3" / "B0-002__1_attr1_subject.png"
        src_file2.write_text("image2")

        src_file3 = temp_dir / "SomeProject" / "Aiarty_Images" / "Batch_Export_Case3" / "C0-003__1_attr1_subject.png"
        src_file3.write_text("image3")

        src_file4 = temp_dir / "SomeProject" / "Aiarty_Images" / "Batch_Export_Case3" / "D0-004__1_attr1_subject.png"
        src_file4.write_text("image4")

        # 构造模块1数据项
        items = [
            MatchedImageItem(file_path=src_file1, folder_path=src_file1.parent, original_name=src_file1.name, is_valid=True, logical_parent="B0-001", sequence_num="1", extension=".png", target_name="B0-001__1.png", status_message="待重命名"),
            MatchedImageItem(file_path=src_file2, folder_path=src_file2.parent, original_name=src_file2.name, is_valid=True, logical_parent="B0-002", sequence_num="1", extension=".png", target_name="B0-002__1.png", status_message="待重命名"),
            MatchedImageItem(file_path=src_file3, folder_path=src_file3.parent, original_name=src_file3.name, is_valid=True, logical_parent="C0-003", sequence_num="1", extension=".png", target_name="C0-003__1.png", status_message="待重命名"),
            MatchedImageItem(file_path=src_file4, folder_path=src_file4.parent, original_name=src_file4.name, is_valid=True, logical_parent="D0-004", sequence_num="1", extension=".png", target_name="D0-004__1.png", status_message="待重命名"),
        ]

        m2 = Module2Widget()
        m2.set_locked(False)
        m2.set_source_items(items)
        m2.left_drop_zone.set_folder(root_folder)

        # 执行分析
        m2._run_analysis(root_folder)

        table = m2.right_table.table
        assert table.columnCount() == 4, f"Expected 4 columns, got {table.columnCount()}"
        assert [table.horizontalHeaderItem(i).text() for i in range(4)] == ["序号", "原文件", "预期重命名", "状态"]
        print("Header and 4-column structure verified [OK]")

        results = m2.right_table.trace_items
        assert len(results) == 4

        # 验证项1: 正常唯一定位 -> 即将被写入到[XXXX]
        row0_orig = table.item(0, 1).text()
        row0_expected = table.item(0, 2).text()
        row0_status = table.item(0, 3).text()
        print(f"Row 0: orig='{row0_orig}', expected='{row0_expected}', status='{row0_status}'")
        assert row0_orig == "B0-001__1_attr1_subject.png", f"Expected filename only in Field 2, got {row0_orig}"
        assert row0_expected == "B0-001__1.png"
        assert row0_status == "即将被写入到[A_Prefab\\Bracelet\\B0-001]"
        assert results[0].status_type == "normal"
        print("Test Case 1 (Normal Write Path with Brackets & Pure Filename) [OK]")

        # 验证项2: 同名文件已存在 -> 即将被写入到[XXXX](同名文件将覆盖!)
        row1_orig = table.item(1, 1).text()
        row1_expected = table.item(1, 2).text()
        row1_status = table.item(1, 3).text()
        print(f"Row 1: orig='{row1_orig}', expected='{row1_expected}', status='{row1_status}'")
        assert row1_orig == "B0-002__1_attr1_subject.png"
        assert row1_expected == "B0-002__1.png"
        assert row1_status == "即将被写入到[A_Prefab\\Rings\\B0-002](同名文件将覆盖!)"
        assert results[1].status_type == "override"
        print("Test Case 2 (File Override Detection with Brackets & Pure Filename) [OK]")

        # 验证项3: 同名文件夹不唯一
        row2_status = table.item(2, 3).text()
        print(f"Row 2: status='{row2_status}'")
        assert row2_status == "同名文件夹不唯一"
        assert results[2].status_type == "error"
        print("Test Case 3 (Ambiguous Folder Detection) [OK]")

        # 验证项4: 无法找到
        row3_status = table.item(3, 3).text()
        print(f"Row 3: status='{row3_status}'")
        assert row3_status == "无法找到"
        assert results[3].status_type == "error"
        print("Test Case 4 (Not Found Detection) [OK]")

    print("\nALL ENHANCED 4-COLUMN LOGIC TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()

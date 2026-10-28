"""
Test Suite for Tab 2: Aiarty Image Enhancer Page
Verifies:
1. EnhancerWorkflowPage instantiation and UI components.
2. FolderDropZoneWidget (empty guidance, clear, recursive checkbox, scan button).
3. EnhancerResultTableWidget (image list, 5-column structure, '只显示有效' checkbox).
4. Image scanning functionality and matching rule [逻辑父文件夹名]__[纯数字序号].png.
"""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from src.ui.pages.enhancer_page import EnhancerWorkflowPage


def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # 构造测试子文件夹体系与图片文件
        sub1 = temp_dir / "Enhance_Batch_1"
        sub1.mkdir(parents=True)
        (sub1 / "B0-001__1.png").write_bytes(b"PNG1")        # 有效
        (sub1 / "img_002.jpg").write_bytes(b"JPG2")          # 无效 (非 png)

        nested_sub = sub1 / "nested_folder"
        nested_sub.mkdir(parents=True)
        (nested_sub / "ABc00-101__0123.png").write_bytes(b"PNG3")  # 有效
        (nested_sub / "0B-001__1.png").write_bytes(b"PNG4")        # 无效 (数字在字母前)
        (nested_sub / "readme.txt").write_text("NOT_AN_IMAGE")     # 非图片 (排除)

        page = EnhancerWorkflowPage()

        # 1. 验证左侧子文件夹拖入区
        left_zone = page.left_drop_zone
        assert left_zone.placeholder_tip.text() == "拖拽子文件夹到此处"
        assert "支持逐一拖入" in left_zone.placeholder_subtip.text()
        assert left_zone.recursive_checkbox.isChecked() is True, "Recursive checkbox should be checked by default"
        assert left_zone.clear_btn.isHidden() is True, "Clear button should be hidden when empty"
        assert left_zone.scan_btn.isHidden() is True, "Scan button should be hidden when empty"
        print("Empty drop zone state & recursive checkbox verified [OK]")

        # 2. 模拟拖入子文件夹
        left_zone.add_folder(sub1)
        assert not left_zone.clear_btn.isHidden(), "Clear button should appear after folder is added"
        assert not left_zone.scan_btn.isHidden(), "Scan button should appear after folder is added"
        print("Drop zone folder added state (Clear & Scan buttons shown) [OK]")

        # 3. 验证右侧图片列表结构（5 列）
        right_table = page.right_table
        assert right_table.title_label.text() == "图片列表"
        assert right_table.only_valid_checkbox.text() == "只显示有效"
        assert right_table.only_valid_checkbox.isChecked() is False
        assert right_table.table.columnCount() == 5
        assert "规则: [逻辑父名]__[纯数字序号].png" in right_table.rule_tag.text()
        assert right_table.rule_example_btn is not None
        print("Right table 5-column structure & rule badge verified [OK]")

        # 4. 执行扫描（递归模式）
        page._start_scanning([sub1], recursive=True)
        page.thread_pool.waitForDone(5000)
        app.processEvents()

        # 校验扫描结果（应该包含 4 张图片，排除 txt 文件）
        items = right_table.image_items
        assert len(items) == 4, f"Expected 4 images, got {len(items)}"
        names = [it.original_name for it in items]
        assert "B0-001__1.png" in names
        assert "img_002.jpg" in names
        assert "ABc00-101__0123.png" in names
        assert "0B-001__1.png" in names
        assert "readme.txt" not in names

        # 校验有效与无效判定
        item_map = {it.original_name: it for it in items}
        assert item_map["B0-001__1.png"].is_valid is True
        assert item_map["B0-001__1.png"].logical_parent == "B0-001"
        assert item_map["B0-001__1.png"].sequence_num == "1"
        assert item_map["B0-001__1.png"].status_message == "有效"

        assert item_map["ABc00-101__0123.png"].is_valid is True
        assert item_map["ABc00-101__0123.png"].logical_parent == "ABc00-101"
        assert item_map["ABc00-101__0123.png"].sequence_num == "0123"
        assert item_map["ABc00-101__0123.png"].status_message == "有效"

        assert item_map["img_002.jpg"].is_valid is False
        assert item_map["img_002.jpg"].status_message == "无效"

        assert item_map["0B-001__1.png"].is_valid is False
        assert item_map["0B-001__1.png"].status_message == "无效"
        print("Recursive image scan results & rule validation (2 valid, 2 invalid) [OK]")

        # 5. 验证“只显示有效”筛选过滤
        assert right_table.table.rowCount() == 4
        right_table.only_valid_checkbox.setChecked(True)
        app.processEvents()
        assert right_table.table.rowCount() == 2, f"Expected 2 rows under valid filter, got {right_table.table.rowCount()}"

        right_table.only_valid_checkbox.setChecked(False)
        app.processEvents()
        assert right_table.table.rowCount() == 4
        print("'只显示有效' filter toggle verified [OK]")

        # 6. 验证清空联动
        left_zone.clear_all()
        assert len(right_table.image_items) == 0, "Right table should be empty after clear_all"
        assert left_zone.clear_btn.isHidden() is True
        assert left_zone.scan_btn.isHidden() is True
        print("Clear all folders and table sync verified [OK]")

    print("\nALL ENHANCER WORKFLOW PAGE TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()

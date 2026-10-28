"""
Unit tests for tab switching reset behavior between:
- Aiarty Image Matting（抠图）
- Aiarty Image Enhancer（画质增强）

Requirement:
从一个模块切换到另一个模块，原始模块与目标模块都回到初始重置状态。
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.ui.pages.enhancer_result_table import EnhancerImageItem
from src.config import MatchedImageItem


def test_tab_switch_reset():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()

    temp_dir = Path(tempfile.mkdtemp(prefix="test_tab_reset_"))
    try:
        sub1 = temp_dir / "sub1"
        sub1.mkdir(parents=True)
        img1 = sub1 / "test_01.png"
        img1.write_bytes(b"dummy")

        # 1. 在 Matting 模块中灌入测试数据并解锁模块 2
        matting = win.matting_page
        matting.module1_widget.left_drop_zone.add_folder(sub1)
        assert len(matting.module1_widget.left_drop_zone.folder_list) == 1

        mock_matched = [
            MatchedImageItem(
                file_path=img1,
                folder_path=sub1,
                folder_display_name="sub1",
                original_name="test_01.png",
                logical_parent="sub1",
                sequence_num="1",
                target_name="sub1__1.png",
                is_valid=True,
                status_message="待重命名"
            )
        ]
        matting.module1_widget.right_result_table.set_results(mock_matched)
        assert len(matting.module1_widget.right_result_table.matched_items) == 1

        # 解锁模块 2
        matting.module2_widget.set_source_items([mock_matched[0]])
        matting.module2_widget.set_locked(False)
        matting.module2_widget.left_drop_zone.set_folder(temp_dir)
        assert not matting.module2_widget.is_locked
        assert matting.module2_widget.left_drop_zone.selected_folder == temp_dir

        # 2. 切换到 Enhancer（画质增强）
        win.segmented_nav.setCurrentItem("enhancer")
        app.processEvents()

        # 校验：切换后当前页面为 Enhancer
        assert win.stacked_widget.currentIndex() == 1

        # 校验：原始模块（Matting）已全部重置回初始状态
        assert len(matting.module1_widget.left_drop_zone.folder_list) == 0
        assert len(matting.module1_widget.right_result_table.matched_items) == 0
        assert matting.module1_widget.left_drop_zone.recursive_checkbox.isChecked()
        assert not matting.module1_widget.right_result_table.only_valid_checkbox.isChecked()
        assert matting.module2_widget.is_locked
        assert matting.module2_widget.left_drop_zone.selected_folder is None
        assert len(matting.module2_widget.right_table.trace_items) == 0

        # 校验：目标模块（Enhancer）也处于干净的初始重置状态
        enhancer = win.enhancer_page
        assert len(enhancer.left_drop_zone.folder_list) == 0
        assert len(enhancer.right_table.image_items) == 0
        assert enhancer.left_drop_zone.recursive_checkbox.isChecked()
        assert not enhancer.right_table.only_valid_checkbox.isChecked()
        print("Switch to Enhancer: Matting source reset & Enhancer target clean [OK]")

        # 3. 在 Enhancer 中注入测试数据
        enhancer.left_drop_zone.add_folder(sub1)
        assert len(enhancer.left_drop_zone.folder_list) == 1

        mock_enhancer_items = [
            EnhancerImageItem(
                file_path=img1,
                folder_path=sub1,
                folder_display_name="sub1",
                original_name="test_01.png",
                is_valid=True,
                status_message="待处理"
            )
        ]
        enhancer.right_table.set_results(mock_enhancer_items)
        assert len(enhancer.right_table.image_items) == 1

        # 4. 切换回 Matting（抠图）
        win.segmented_nav.setCurrentItem("matting")
        app.processEvents()

        # 校验：当前页面为 Matting
        assert win.stacked_widget.currentIndex() == 0

        # 校验：原始模块（Enhancer）已全部重置回初始状态
        assert len(enhancer.left_drop_zone.folder_list) == 0
        assert len(enhancer.right_table.image_items) == 0
        assert enhancer.left_drop_zone.recursive_checkbox.isChecked()
        assert not enhancer.right_table.only_valid_checkbox.isChecked()

        # 校验：目标模块（Matting）也处于初始重置状态
        assert len(matting.module1_widget.left_drop_zone.folder_list) == 0
        assert len(matting.module1_widget.right_result_table.matched_items) == 0
        assert matting.module2_widget.is_locked
        assert matting.module2_widget.left_drop_zone.selected_folder is None
        assert len(matting.module2_widget.right_table.trace_items) == 0
        print("Switch back to Matting: Enhancer source reset & Matting target clean [OK]")

        # 5. 多次连续切换幂等性校验
        win.segmented_nav.setCurrentItem("enhancer")
        app.processEvents()
        assert win.stacked_widget.currentIndex() == 1
        win.segmented_nav.setCurrentItem("matting")
        app.processEvents()
        assert win.stacked_widget.currentIndex() == 0
        print("Multiple idempotent switches verified [OK]")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        win.close()


if __name__ == "__main__":
    test_tab_switch_reset()
    print("\nALL TAB SWITCH RESET TESTS PASSED SUCCESSFULLY!")

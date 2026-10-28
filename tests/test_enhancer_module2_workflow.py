"""
Unit test for Enhancer Module 1 -> Transfer Button -> Module 2 Unlock & Copy Workflow:
Verifies:
1. When Module 1 has NO valid images:
   - Clicking "准备复制到[逻辑父文件夹]" keeps Module 2 locked and warns "抱歉，没有有效图片可以转移".
2. When Module 1 HAS valid images:
   - Clicking "准备复制到[逻辑父文件夹]" unlocks Module 2 and injects valid items.
3. Module 2 functionality (identical to Matting Module 2):
   - Analyzing source parent directory
   - Tracing matches (normal, override)
   - Executing physical copy and disabling copy button.
"""
import sys
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from src.ui.pages.enhancer_page import EnhancerWorkflowPage
from src.config import EnhancerImageItem


def test_enhancer_module2_workflow():
    app = QApplication.instance() or QApplication(sys.argv)
    temp_dir = Path(tempfile.mkdtemp(prefix="test_enhancer_m2_"))

    try:
        page = EnhancerWorkflowPage()
        page.show()
        app.processEvents()

        # 初始状态：模块 2 必须处于锁定状态
        assert page.module2_widget.is_locked is True, "Module 2 should initially be locked"
        print("Initial Module 2 locked state verified [OK]")

        # -------------------------------------------------------------
        # 测试场景 1：无有效图片时点击「准备复制到[逻辑父文件夹]」
        # -------------------------------------------------------------
        invalid_item = EnhancerImageItem(
            file_path=temp_dir / "invalid.jpg",
            folder_path=temp_dir,
            original_name="invalid.jpg",
            is_valid=False,
            logical_parent="-",
            sequence_num="-",
            status_message="无效"
        )
        page.right_table.set_results([invalid_item])
        app.processEvents()

        page.prepare_transfer_btn.click()
        app.processEvents()

        # 模块 2 依然处于锁定状态
        assert page.module2_widget.is_locked is True, "Module 2 should stay locked when no valid images"
        print("Test Case 1: No valid images -> Module 2 stays locked [OK]")

        # -------------------------------------------------------------
        # 测试场景 2：有有效图片时点击「准备复制到[逻辑父文件夹]」
        # -------------------------------------------------------------
        # 创建待复制的原图片
        src_folder = temp_dir / "source_scanned"
        src_folder.mkdir(parents=True)
        img1_file = src_folder / "B0-001__1.png"
        img1_file.write_bytes(b"ENHANCED_IMAGE_DATA_1")

        valid_item = EnhancerImageItem(
            file_path=img1_file,
            folder_path=src_folder,
            original_name="B0-001__1.png",
            is_valid=True,
            logical_parent="B0-001",
            sequence_num="1",
            target_name="B0-001__1.png",
            status_message="有效"
        )
        page.right_table.set_results([valid_item, invalid_item])
        app.processEvents()

        page.prepare_transfer_btn.click()
        app.processEvents()

        # 校验：模块 2 成功解锁，且仅注入有效图片
        assert page.module2_widget.is_locked is False, "Module 2 should be unlocked with valid images"
        assert len(page.module2_widget.source_module1_items) == 1
        assert page.module2_widget.source_module1_items[0].original_name == "B0-001__1.png"
        print("Test Case 2: Valid images present -> Module 2 successfully unlocked [OK]")

        # -------------------------------------------------------------
        # 测试场景 3：模块 2 溯源分析与复制执行（逻辑与抠图模块2完全一致）
        # -------------------------------------------------------------
        # 创建目标源文件夹结构：target_root / Bracelet / B0-001
        target_root = temp_dir / "target_root"
        matched_dest_folder = target_root / "Bracelet" / "B0-001"
        matched_dest_folder.mkdir(parents=True)

        # 设置源文件夹并执行分析
        page.module2_widget.left_drop_zone.set_folder(target_root)
        app.processEvents()

        page.module2_widget._run_analysis(target_root)
        app.processEvents()

        trace_table = page.module2_widget.right_table
        assert len(trace_table.trace_items) == 1
        trace_item = trace_table.trace_items[0]
        assert trace_item.logical_parent == "B0-001"
        assert trace_item.status_type == "normal"
        assert "即将被写入到[" in trace_item.status_display
        assert "B0-001]" in trace_item.status_display
        assert trace_table.copy_btn.isEnabled() is True
        print("Test Case 3: Module 2 trace analysis matched B0-001 [OK]")

        # 执行文件复制
        trace_table.copy_btn.click()
        page.module2_widget.thread_pool.waitForDone(5000)
        app.processEvents()

        # 校验物理文件已被复制到目标文件夹
        copied_target_file = matched_dest_folder / "B0-001__1.png"
        assert copied_target_file.exists() is True
        assert copied_target_file.read_bytes() == b"ENHANCED_IMAGE_DATA_1"

        # 校验复制完成后按钮变灰为“已全部复制”
        assert trace_table.copy_btn.isEnabled() is False
        assert trace_table.copy_btn.text() == "已全部复制"
        print("Test Case 4: Physical copy executed & copy button disabled [OK]")

        # -------------------------------------------------------------
        # 测试场景 4：模块 1 变动导致模块 2 自动重置并上锁
        # -------------------------------------------------------------
        page.left_drop_zone.clear_all()
        app.processEvents()

        assert page.module2_widget.is_locked is True, "Module 2 should re-lock when Module 1 cleared"
        assert len(page.module2_widget.source_module1_items) == 0
        assert page.module2_widget.left_drop_zone.selected_folder is None
        assert len(page.module2_widget.right_table.trace_items) == 0
        print("Test Case 5: Module 1 clear -> Module 2 resets and locks [OK]")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        page.close()


if __name__ == "__main__":
    test_enhancer_module2_workflow()
    print("\nALL ENHANCER MODULE 2 WORKFLOW TESTS PASSED SUCCESSFULLY!")

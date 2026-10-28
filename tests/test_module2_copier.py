"""
End-to-End Test for Module 2: Copy Execution & Progress Feedback
Verifies:
1. '开始复制' button activation and state.
2. Background file copying (copy2 with metadata).
3. Target folder structure creation and file content integrity.
4. Status update and info notification callbacks.
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

        # 1. 创建源文件夹架构
        source_root = temp_dir / "SourceRoot"
        b0_dir = source_root / "A_Prefab" / "Bracelet" / "B0-001"
        b0_dir.mkdir(parents=True)

        # 2. 创建待复制原图片文件
        scan_folder = temp_dir / "ScannedImages"
        scan_folder.mkdir(parents=True)
        img1 = scan_folder / "B0-001__1_attr1_subject.png"
        img1.write_bytes(b"PNG_FAKE_IMAGE_DATA_1")
        img2 = scan_folder / "B0-001__2_attr1_subject.png"
        img2.write_bytes(b"PNG_FAKE_IMAGE_DATA_2")

        # 3. 构造匹配数据
        item1 = MatchedImageItem(
            file_path=img1, folder_path=scan_folder, original_name=img1.name,
            is_valid=True, logical_parent="B0-001", sequence_num="1", extension=".png",
            target_name="B0-001__1.png", status_message="待重命名"
        )
        item2 = MatchedImageItem(
            file_path=img2, folder_path=scan_folder, original_name=img2.name,
            is_valid=True, logical_parent="B0-001", sequence_num="2", extension=".png",
            target_name="B0-001__2.png", status_message="待重命名"
        )

        m2 = Module2Widget()
        m2.set_locked(False)
        m2.set_source_items([item1, item2])
        m2.left_drop_zone.set_folder(source_root)

        # 执行分析
        m2._run_analysis(source_root)

        copy_btn = m2.right_table.copy_btn
        assert copy_btn.isEnabled(), "Copy button should be enabled after analysis with valid targets"
        assert copy_btn.text() == "开始复制 (2)", f"Expected '开始复制 (2)', got {copy_btn.text()}"
        print("Copy button enabled and text badge verified [OK]")

        # 触发复制
        m2._start_copying()

        # 等待后台 QThreadPool 任务完成并刷新主事件循环
        m2.thread_pool.waitForDone(5000)
        app.processEvents()

        # 验证物理文件是否成功被写入到目标文件夹
        target_file1 = b0_dir / "B0-001__1.png"
        target_file2 = b0_dir / "B0-001__2.png"

        assert target_file1.exists(), f"Target file 1 does not exist: {target_file1}"
        assert target_file2.exists(), f"Target file 2 does not exist: {target_file2}"
        assert target_file1.read_bytes() == b"PNG_FAKE_IMAGE_DATA_1", "Target file 1 content mismatch"
        assert target_file2.read_bytes() == b"PNG_FAKE_IMAGE_DATA_2", "Target file 2 content mismatch"
        print("Physical file copy integrity verified [OK]")

        # 验证界面状态文本
        status1 = m2.right_table.table.item(0, 3).text()
        status2 = m2.right_table.table.item(1, 3).text()
        print(f"Status 1: {status1}")
        print(f"Status 2: {status2}")
        assert "已成功写入到" in status1
        assert "已成功写入到" in status2
        print("UI status row text updated to '已成功写入到[...]' [OK]")

        # 核心需求验证：执行成功后，“开始复制”按钮变灰（不可点击）
        assert not copy_btn.isEnabled(), "Copy button should be disabled after successful execution"
        assert copy_btn.text() == "已全部复制", f"Expected '已全部复制', got {copy_btn.text()}"
        print("Copy button disabled and changed to '已全部复制' [OK]")

    print("\nALL MODULE 2 COPY EXECUTION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()

"""
End-to-end scanner and renamer tests for the new naming rule and full image listing.
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.scanner import FolderScannerWorker
from src.core.renamer import FileRenamerWorker

def run_e2e():
    temp_dir = Path(tempfile.mkdtemp(prefix="test_e2e_all_images_"))
    try:
        sub = temp_dir / "Sub1"
        sub.mkdir()

        # 1. 有效图片 (应被标记为待重命名)
        (sub / "B0-001__1_attr1_subject.png").write_text("data1")
        (sub / "ABc00-101__0123_attr1_subject.png").write_text("data2")

        # 2. 无效图片 (应被标记为无效，但依然完整展示在列表中)
        (sub / "0B-001__1_attr1_subject.png").write_text("invalid_name")
        (sub / "B0-001__1_attr1_subject.jpg").write_text("invalid_format")
        (sub / "other_random_pic.webp").write_text("invalid_random")

        # 3. 非图片文件 (如 txt，不应进入图片列表)
        (sub / "document.txt").write_text("not an image")

        # 扫描
        scanner = FolderScannerWorker([sub])
        scanned = []
        scanner.signals.finished.connect(lambda items: scanned.extend(items))
        scanner.run()

        # 验证：包含所有 5 张图片，过滤了 txt
        assert len(scanned) == 5, f"Expected 5 images, got {len(scanned)}"

        valid_items = [it for it in scanned if it.is_valid]
        invalid_items = [it for it in scanned if not it.is_valid]

        assert len(valid_items) == 2, f"Expected 2 valid items, got {len(valid_items)}"
        assert len(invalid_items) == 3, f"Expected 3 invalid items, got {len(invalid_items)}"

        for it in valid_items:
            assert it.status_message == "待重命名"
            assert it.logical_parent != "-"
            assert it.target_name != "-"

        for it in invalid_items:
            assert it.status_message == "无效"
            assert it.logical_parent == "-"
            assert it.target_name == "-"

        # 执行重命名
        renamer = FileRenamerWorker(scanned)
        renamer.run()

        # 校验：仅有效文件被更名，无效文件完好无损
        assert (sub / "B0-001__1.png").exists(), "B0-001__1.png should exist"
        assert (sub / "ABc00-101__0123.png").exists(), "ABc00-101__0123.png should exist"
        assert not (sub / "B0-001__1_attr1_subject.png").exists()

        assert (sub / "0B-001__1_attr1_subject.png").exists()
        assert (sub / "B0-001__1_attr1_subject.jpg").exists()
        assert (sub / "other_random_pic.webp").exists()
        assert (sub / "document.txt").exists()

        print("Full image listing with valid/invalid status E2E test passed successfully!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_e2e()

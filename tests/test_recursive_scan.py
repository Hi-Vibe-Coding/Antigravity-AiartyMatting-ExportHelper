"""
Unit tests for recursive vs shallow scanning mode and checkbox behavior.
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.scanner import FolderScannerWorker

def run_tests():
    temp_dir = Path(tempfile.mkdtemp(prefix="test_recursive_"))
    try:
        # 创建多层嵌套目录结构
        root_dir = temp_dir / "RootFolder"
        root_dir.mkdir()
        level1_dir = root_dir / "Level1"
        level1_dir.mkdir()
        level2_dir = level1_dir / "Level2"
        level2_dir.mkdir()

        # 第 1 层图片
        (root_dir / "B0-001__1_attr1_subject.png").write_text("img0")
        (root_dir / "other0.jpg").write_text("img0_invalid")

        # 第 2 层图片 (Level1)
        (level1_dir / "ABc00-101__2_attr1_subject.png").write_text("img1")

        # 第 3 层图片 (Level2)
        (level2_dir / "XYZ99-202__3_attr1_subject.png").write_text("img2")
        (level2_dir / "deep_invalid.png").write_text("img2_invalid")

        # 测试 A: 递归扫描模式 (recursive=True)
        scanner_rec = FolderScannerWorker([root_dir], recursive=True)
        items_rec = []
        scanner_rec.signals.finished.connect(lambda items: items_rec.extend(items))
        scanner_rec.run()

        # 预期：找到全部 5 张图片（含深层嵌套）
        assert len(items_rec) == 5, f"Expected 5 items in recursive scan, got {len(items_rec)}"
        valid_rec = [i for i in items_rec if i.is_valid]
        assert len(valid_rec) == 3, f"Expected 3 valid items in recursive scan, got {len(valid_rec)}"
        parents = {i.logical_parent for i in valid_rec}
        assert parents == {"B0-001", "ABc00-101", "XYZ99-202"}
        print("Test A (recursive=True) passed successfully!")

        # 测试 B: 非递归扫描模式 (recursive=False)
        scanner_shallow = FolderScannerWorker([root_dir], recursive=False)
        items_shallow = []
        scanner_shallow.signals.finished.connect(lambda items: items_shallow.extend(items))
        scanner_shallow.run()

        # 预期：仅找到第 1 层的 2 张图片
        assert len(items_shallow) == 2, f"Expected 2 items in shallow scan, got {len(items_shallow)}"
        valid_shallow = [i for i in items_shallow if i.is_valid]
        assert len(valid_shallow) == 1, f"Expected 1 valid item in shallow scan, got {len(valid_shallow)}"
        assert valid_shallow[0].logical_parent == "B0-001"
        print("Test B (recursive=False) passed successfully!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_tests()

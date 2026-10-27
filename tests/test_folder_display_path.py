"""
Unit test for accurate upper-level folder path calculation in Result Table.
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.scanner import FolderScannerWorker
from src.core.renamer import FileRenamerWorker

def run_tests():
    temp_dir = Path(tempfile.mkdtemp(prefix="test_upper_path_"))
    try:
        # 模拟结构：Batch_Export_案例3 作为拖入的根文件夹
        dragged_root = temp_dir / "Batch_Export_案例3"
        dragged_root.mkdir()

        nested_dir = dragged_root / "新建文件夹"
        nested_dir.mkdir()

        deep_dir = nested_dir / "Level2"
        deep_dir.mkdir()

        # 1. 拖入根目录下的图片
        (dragged_root / "3-1_attr1.png").write_text("data1")

        # 2. 嵌套子文件夹下的有效图片
        (nested_dir / "B0-001__2_attr1_subject.png").write_text("data2")

        # 3. 更深层嵌套图片
        (deep_dir / "ABc00-101__1_attr1_subject.png").write_text("data3")

        # 执行递归扫描
        scanner = FolderScannerWorker([dragged_root], recursive=True)
        items = []
        scanner.signals.finished.connect(lambda r: items.extend(r))
        scanner.run()

        assert len(items) == 3, f"Expected 3 items, got {len(items)}"

        # 查找各个项
        item1 = next(it for it in items if it.original_name == "3-1_attr1.png")
        item2 = next(it for it in items if it.original_name == "B0-001__2_attr1_subject.png")
        item3 = next(it for it in items if it.original_name == "ABc00-101__1_attr1_subject.png")

        # 规范化反斜杠比较
        expected_path1 = str(Path("Batch_Export_案例3"))
        expected_path2 = str(Path("Batch_Export_案例3/新建文件夹"))
        expected_path3 = str(Path("Batch_Export_案例3/新建文件夹/Level2"))

        assert item1.folder_display_name == expected_path1, f"Mismatch item1: {item1.folder_display_name} != {expected_path1}"
        assert item2.folder_display_name == expected_path2, f"Mismatch item2: {item2.folder_display_name} != {expected_path2}"
        assert item3.folder_display_name == expected_path3, f"Mismatch item3: {item3.folder_display_name} != {expected_path3}"

        print(f"item1 display folder: {item1.folder_display_name} [OK]")
        print(f"item2 display folder: {item2.folder_display_name} [OK]")
        print(f"item3 display folder: {item3.folder_display_name} [OK]")

        # 测试重命名依然在正确真实路径执行
        valid_items = [it for it in items if it.is_valid]
        assert len(valid_items) == 2
        renamer = FileRenamerWorker(valid_items)
        renamer.run()

        assert (nested_dir / "B0-001__2.png").exists(), "Renamed file should exist in nested_dir"
        assert (deep_dir / "ABc00-101__1.png").exists(), "Renamed file should exist in deep_dir"
        assert not (nested_dir / "B0-001__2_attr1_subject.png").exists()

        print("Folder display path test passed successfully!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_tests()

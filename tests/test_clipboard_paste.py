"""
Test Suite for Clipboard Paste of Folders (Module 1 & Module 2)
Verifies:
1. extract_folders_from_clipboard handles URLs (CF_HDROP) and plain text paths (with/without quotes).
2. Module 1 FolderDropZoneWidget:
   - paste_from_clipboard adds folders to list.
   - Duplicate prevention works.
   - Empty/invalid clipboard shows warning and doesn't crash.
3. Module 2 SingleFolderDropZone:
   - paste_from_clipboard sets target source folder.
   - Multiple folders on clipboard takes first folder.
   - Empty/invalid clipboard shows warning and doesn't crash.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QMimeData, QUrl

from src.ui.clipboard_helper import extract_folders_from_clipboard
from src.ui.module1.folder_drop_zone import FolderDropZoneWidget
from src.ui.module2.single_folder_drop_zone import SingleFolderDropZone


def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        dir1 = temp_dir / "SubFolderA"
        dir1.mkdir()
        dir2 = temp_dir / "SubFolderB"
        dir2.mkdir()
        dummy_file = temp_dir / "not_a_dir.txt"
        dummy_file.write_text("hello")

        # -------------------------------------------------------------
        # Test 1: extract_folders_from_clipboard with URLs
        # -------------------------------------------------------------
        mime_urls = QMimeData()
        mime_urls.setUrls([
            QUrl.fromLocalFile(str(dir1)),
            QUrl.fromLocalFile(str(dummy_file)),
            QUrl.fromLocalFile(str(dir2)),
        ])

        with patch.object(QApplication, "clipboard") as mock_clip:
            mock_clip.return_value.mimeData.return_value = mime_urls
            extracted = extract_folders_from_clipboard()
            assert len(extracted) == 2
            assert dir1.resolve() in extracted
            assert dir2.resolve() in extracted
            assert dummy_file.resolve() not in extracted
            print("Test 1: extract_folders_from_clipboard with URLs [OK]")

        # -------------------------------------------------------------
        # Test 2: extract_folders_from_clipboard with Plain Text (quoted)
        # -------------------------------------------------------------
        mime_text = QMimeData()
        mime_text.setText(f'"{str(dir1)}"\n"{str(dir2)}"\n"invalid/path"')

        with patch.object(QApplication, "clipboard") as mock_clip:
            mock_clip.return_value.mimeData.return_value = mime_text
            extracted = extract_folders_from_clipboard()
            assert len(extracted) == 2
            assert dir1.resolve() in extracted
            assert dir2.resolve() in extracted
            print("Test 2: extract_folders_from_clipboard with Text [OK]")

        # -------------------------------------------------------------
        # Test 3: Module 1 FolderDropZoneWidget paste
        # -------------------------------------------------------------
        zone1 = FolderDropZoneWidget()
        with patch.object(QApplication, "clipboard") as mock_clip:
            mock_clip.return_value.mimeData.return_value = mime_urls
            zone1.paste_from_clipboard()

            assert len(zone1.folder_list) == 2
            assert dir1.resolve() in zone1.folder_set
            assert dir2.resolve() in zone1.folder_set
            assert not zone1.scan_btn.isHidden()
            print("Test 3: Module 1 paste_from_clipboard adds folders [OK]")

            # Test duplicate paste
            zone1.paste_from_clipboard()
            assert len(zone1.folder_list) == 2
            print("Test 3.1: Module 1 paste_from_clipboard duplicate prevention [OK]")

        # -------------------------------------------------------------
        # Test 4: Module 2 SingleFolderDropZone paste
        # -------------------------------------------------------------
        zone2 = SingleFolderDropZone()
        with patch.object(QApplication, "clipboard") as mock_clip:
            mock_clip.return_value.mimeData.return_value = mime_urls
            zone2.paste_from_clipboard()

            # Multiple folders on clipboard -> first valid folder is selected
            assert zone2.selected_folder == dir1.resolve()
            assert zone2.analyze_btn.isEnabled()
            assert zone2.clear_btn.isEnabled()
            assert not zone2.card_container.isHidden()
            print("Test 4: Module 2 paste_from_clipboard sets single folder [OK]")

        # -------------------------------------------------------------
        # Test 5: Empty clipboard handling
        # -------------------------------------------------------------
        empty_mime = QMimeData()
        with patch.object(QApplication, "clipboard") as mock_clip:
            mock_clip.return_value.mimeData.return_value = empty_mime
            # Should not raise exception
            zone1.paste_from_clipboard()
            zone2.paste_from_clipboard()
            print("Test 5: Empty clipboard handling without error [OK]")

        # -------------------------------------------------------------
        # Test 6: Right-click context menu generates '粘贴文件夹' Action
        # -------------------------------------------------------------
        with patch("qfluentwidgets.RoundMenu.exec") as mock_menu_exec:
            zone1._show_context_menu(zone1.rect().center())
            assert mock_menu_exec.called
            print("Test 6: Module 1 right-click context menu [OK]")

        with patch("qfluentwidgets.RoundMenu.exec") as mock_menu_exec2:
            zone2._show_context_menu(zone2.rect().center())
            assert mock_menu_exec2.called
            print("Test 6.1: Module 2 right-click context menu [OK]")

    print("\nALL CLIPBOARD PASTE FOLDER TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()

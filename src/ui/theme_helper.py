"""
Theme helper module for consistent Dark / Light mode styling across Qt & Fluent widgets.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from qfluentwidgets import isDarkTheme


def apply_app_palette(is_dark: bool = None):
    """
    更新全局 QApplication 的 QPalette，确保标准 Qt 控件（如 Table 单元格、Header、系统组件）
    在深色和浅色模式下拥有极高对比度，彻底杜绝看不清的问题。
    """
    if is_dark is None:
        is_dark = isDarkTheme()

    app = QApplication.instance()
    if not app:
        return

    palette = QPalette()
    if is_dark:
        bg_main = QColor("#202020")
        bg_card = QColor("#2b2b2b")
        bg_alt = QColor("#323232")
        text_primary = QColor("#ffffff")
        text_secondary = QColor("#cccccc")
        accent = QColor("#0078d4")

        palette.setColor(QPalette.ColorRole.Window, bg_main)
        palette.setColor(QPalette.ColorRole.WindowText, text_primary)
        palette.setColor(QPalette.ColorRole.Base, bg_card)
        palette.setColor(QPalette.ColorRole.AlternateBase, bg_alt)
        palette.setColor(QPalette.ColorRole.ToolTipBase, bg_card)
        palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
        palette.setColor(QPalette.ColorRole.Text, text_primary)
        palette.setColor(QPalette.ColorRole.Button, bg_card)
        palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff4d4f"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#4cc2ff"))
        palette.setColor(QPalette.ColorRole.Highlight, accent)
        palette.setColor(QPalette.ColorRole.HighlightedText, text_primary)
    else:
        bg_main = QColor("#f3f3f3")
        bg_card = QColor("#ffffff")
        bg_alt = QColor("#f8f8f8")
        text_primary = QColor("#1f1f1f")
        text_secondary = QColor("#5f5f5f")
        accent = QColor("#0078d4")

        palette.setColor(QPalette.ColorRole.Window, bg_main)
        palette.setColor(QPalette.ColorRole.WindowText, text_primary)
        palette.setColor(QPalette.ColorRole.Base, bg_card)
        palette.setColor(QPalette.ColorRole.AlternateBase, bg_alt)
        palette.setColor(QPalette.ColorRole.ToolTipBase, bg_card)
        palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
        palette.setColor(QPalette.ColorRole.Text, text_primary)
        palette.setColor(QPalette.ColorRole.Button, bg_card)
        palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff4d4f"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#0067b8"))
        palette.setColor(QPalette.ColorRole.Highlight, accent)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    app.setPalette(palette)


def get_window_qss(is_dark: bool) -> str:
    """返回主窗口与背景层的全局 QSS 样式"""
    if is_dark:
        return """
            QMainWindow, QWidget#centralWidget {
                background-color: #202020;
                color: #ffffff;
            }
        """
    else:
        return """
            QMainWindow, QWidget#centralWidget {
                background-color: #f3f3f3;
                color: #1f1f1f;
            }
        """

"""
Application Logging and Global Exception Interception Mechanism
Provides:
1. File & Console logging (rotating log file at logs/app.log)
2. sys.excepthook interception to log uncaught exceptions with full tracebacks
3. Friendly error dialog when unhandled crash occurs
"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QApplication

# 日志输出目录（存放在项目根目录下的 logs 文件夹中）
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logger = logging.getLogger("ExportHelper")


def setup_logger():
    """初始化全局日志记录器"""
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 Handler
    if logger.handlers:
        return logger

    # 1. 滚动文件输出（单个文件最大 5MB，保留 5 个备份）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(threadName)s] (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # 2. 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("应用程序日志系统启动成功")
    logger.info(f"日志文件路径: {LOG_FILE.resolve()}")
    logger.info("=" * 60)

    return logger


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """全局未捕获异常拦截器：将崩溃调用栈记录到日志文件并提示用户"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical("捕获到未处理的严重异常 / 崩溃：\n" + err_msg)

    # 尝试弹出错误对话框（如果 QApplication 存在）
    app = QApplication.instance()
    if app:
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("程序运行异常")
            msg_box.setText(f"抱歉，程序遇到了未捕获的严重错误：\n{exc_value}")
            msg_box.setInformativeText(f"详细错误堆栈已保存至日志文件：\n{LOG_FILE.resolve()}")
            msg_box.setDetailedText(err_msg)
            msg_box.exec()
        except Exception:
            pass


def init_logging_system():
    """一键启用日志与异常捕获"""
    setup_logger()
    sys.excepthook = handle_uncaught_exception

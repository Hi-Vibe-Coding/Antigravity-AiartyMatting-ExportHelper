@echo off
chcp 65001 >nul
title Aiarty Image 导出助手

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未检测到虚拟环境，正在通过系统 Python 创建...
    python -m venv .venv
    call .venv\Scripts\pip.exe install -r requirements.txt
)

echo [启动] 正在启动 Aiarty Image 导出助手...
start "" ".venv\Scripts\pythonw.exe" main.py

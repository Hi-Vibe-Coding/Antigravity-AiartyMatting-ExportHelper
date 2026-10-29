@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Aiarty Image 导出助手

echo ============================================================
echo   Aiarty Image 导出助手 (v1.0.1)
echo ============================================================
echo.

:: 检查并自动初始化 Python 虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [检测] 未检测到本地虚拟环境，正在自动初始化...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [错误] 创建虚拟环境失败！
        echo 请确保系统已安装 Python 3.10+ 并已勾选 "Add Python to PATH"。
        echo.
        pause
        exit /b 1
    )
    echo [安装] 正在安装必要依赖，请稍候...
    call .venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [错误] 安装项目依赖失败，请检查网络连接后重试！
        echo.
        pause
        exit /b 1
    )
    echo [就绪] 虚拟环境初始化完成。
    echo.
)

echo [启动] 正在启动 Aiarty Image 导出助手...
echo [提示] 应用程序运行期间，本控制台窗口将保持开启并输出运行日志。
echo [退出] 如需退出，可直接关闭软件窗口，或在此窗口按下 Ctrl+C。
echo.

:: 使用 python.exe 启动（非 pythonw），控制台全程可见且保留日志
.venv\Scripts\python.exe main.py
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================
if %EXIT_CODE% EQU 0 (
    echo [状态] 应用程序已正常退出。
) else (
    echo [异常] 应用程序异常退出，错误代码: %EXIT_CODE%
    echo 请检查上方控制台日志或 logs\app.log 文件。
)
echo ============================================================
echo.
pause

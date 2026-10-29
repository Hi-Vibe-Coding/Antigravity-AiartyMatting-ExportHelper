@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Aiarty Image 导出助手 - 一键生成独立可执行程序 (.EXE)

echo ============================================================
echo   Aiarty Image 导出助手 (v1.0.0) - 一键打包程序
echo ============================================================
echo.

:: 1. 检查 Python 运行环境
set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
    echo [提示] 未找到本地 .venv 环境，将使用系统全局 Python...
) else (
    echo [检测] 已找到虚拟环境: %PYTHON_EXE%
)

:: 2. 检查 PyInstaller 安装状态
echo [检测] 正在检查 PyInstaller 打包工具...
%PYTHON_EXE% -m pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [安装] 未检测到 PyInstaller，正在自动安装...
    %PYTHON_EXE% -m pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] PyInstaller 安装失败，请检查网络连接！
        echo.
        pause
        exit /b 1
    )
)
echo [就绪] PyInstaller 环境正常。
echo.

:: 3. 清理历史打包生成物
echo [清理] 正在清理旧构建缓存目录 (build / dist)...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "AiartyImageExportHelper.spec" del /f /q "AiartyImageExportHelper.spec"
echo [就绪] 历史缓存清理完毕。
echo.

:: 4. 执行 PyInstaller 打包为纯单文件 EXE
echo ============================================================
echo [开始打包] 正在将项目依赖与资源打包为独立的单个 EXE...
echo 说明：包含 PySide6 界面引擎、QFluentWidgets 视觉资源库等。
echo 耗时约 1~2 分钟，请稍候...
echo ============================================================
echo.

%PYTHON_EXE% -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name "AiartyImageExportHelper" ^
    --paths "." ^
    --collect-all "qfluentwidgets" ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo [失败] 打包过程中出现错误，请检查上方日志输出！
    echo ============================================================
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================================
echo [成功] 打包完成！独立运行文件已生成：
echo 文件路径: dist\AiartyImageExportHelper.exe
echo ============================================================
echo.
echo [说明] 该单个 EXE 文件内置了 Python 解释器与全部依赖库：
echo 1. 可以直接拷贝或发送给其他 Windows 电脑运行；
echo 2. 目标电脑无需安装 Python、无需配置任何开发环境；
echo 3. 双击即可直接启动使用！
echo.
pause

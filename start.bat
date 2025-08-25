@echo off
REM 启动SSH端口转发工具
REM 此脚本假设Python已经安装并添加到PATH中

echo 正在启动Linux SSH端口转发工具...

REM 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python。请安装Python 3.7+并确保已添加到PATH中。
    pause
    exit /b 1
)

REM 检查是否已安装依赖
echo 检查依赖...
pip show PyQt5 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 安装依赖...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo 错误: 安装依赖失败。
        pause
        exit /b 1
    )
)

REM 启动应用
echo 启动应用...
python src\main.py
if %ERRORLEVEL% neq 0 (
    echo 错误: 应用启动失败。
    pause
    exit /b 1
)

exit /b 0
@echo off
REM Windows批处理脚本 - 天眼查爬虫启动脚本

echo ================================
echo 天眼查爬虫启动脚本
echo ================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python环境
    echo 请先安装Python: https://www.python.org/
    pause
    exit /b 1
)

echo ✓ Python环境检测成功
echo.

REM 检查依赖
echo 检查依赖包...
pip list | findstr /C:"selenium" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
) else (
    echo ✓ 依赖包已安装
)

echo.
echo ================================
echo 选择浏览器:
echo 1. Chrome (默认)
echo 2. Edge
echo ================================
echo.

set /p choice=请输入选择 (1或2, 默认1):
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo 使用Chrome浏览器...
    python main.py chrome
) else if "%choice%"=="2" (
    echo 使用Edge浏览器...
    python main.py edge
) else (
    echo 无效的选择
    pause
    exit /b 1
)

pause

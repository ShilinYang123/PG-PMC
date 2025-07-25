@echo off
REM 禁用虚拟环境的批处理脚本
REM 杨老师专用 - 确保使用系统Python

echo === 禁用虚拟环境运行模式 ===

REM 清除虚拟环境变量
set VIRTUAL_ENV=
set VIRTUAL_ENV_PROMPT=

REM 使用系统Python运行脚本
if "%1"=="" (
    echo 用法: no_venv.bat [Python脚本路径]
    echo 示例: no_venv.bat tools\check_structure.py
    pause
    exit /b 1
)

echo 正在使用系统Python运行: %1
python %*

echo.
echo 脚本执行完成
pause

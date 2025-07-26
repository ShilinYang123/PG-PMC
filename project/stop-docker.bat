@echo off
chcp 65001 >nul
echo ========================================
echo PMC全流程管理系统 - Docker停止脚本
echo ========================================
echo.

:: 检查Docker是否运行
echo [1/3] 检查Docker服务状态...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行或未安装
    pause
    exit /b 1
)
echo ✅ Docker服务正常

:: 停止服务
echo [2/3] 停止PMC服务...
docker-compose down
if %errorlevel% neq 0 (
    echo ❌ 服务停止失败
    pause
    exit /b 1
)
echo ✅ 服务停止完成

:: 清理资源（可选）
echo [3/3] 清理选项...
echo.
set /p cleanup="是否清理Docker镜像和卷？(y/N): "
if /i "%cleanup%"=="y" (
    echo 正在清理Docker资源...
    docker-compose down -v --rmi all
    docker system prune -f
    echo ✅ 清理完成
) else (
    echo ℹ️  保留Docker镜像和数据卷
)

echo.
echo ========================================
echo 🛑 PMC系统已停止
echo ========================================
echo.
echo 💡 提示：
echo   - 重新启动: start-docker.bat
echo   - 查看状态: docker-compose ps
echo   - 查看日志: docker-compose logs
echo.
pause
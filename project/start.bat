@echo off
chcp 65001 >nul
echo ========================================
echo PMC全流程管理系统启动脚本
echo ========================================
echo.

:: 检查Docker是否运行
echo [1/5] 检查Docker环境...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker环境正常

:: 检查环境配置文件
echo [2/5] 检查环境配置...
if not exist ".env" (
    echo ⚠️  未找到.env文件，正在复制示例配置...
    copy ".env.example" ".env"
    echo ✅ 已创建.env文件，请根据需要修改配置
) else (
    echo ✅ 环境配置文件存在
)

:: 构建Docker镜像
echo [3/5] 构建Docker镜像...
docker-compose build
if %errorlevel% neq 0 (
    echo ❌ Docker镜像构建失败
    pause
    exit /b 1
)
echo ✅ Docker镜像构建完成

:: 启动数据库服务
echo [4/5] 启动数据库服务...
docker-compose up -d postgres redis
echo ⏳ 等待数据库启动...
timeout /t 10 /nobreak >nul
echo ✅ 数据库服务启动完成

:: 启动所有服务
echo [5/5] 启动所有服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 PMC系统启动成功！
echo ========================================
echo.
echo 📊 前端界面: http://localhost
echo 🔧 后端API: http://localhost:8000
echo 📖 API文档: http://localhost:8000/docs
echo 🗄️  数据库: localhost:5432
echo 🔴 Redis: localhost:6379
echo.
echo 💡 使用以下命令管理服务:
echo    docker-compose logs -f     # 查看日志
echo    docker-compose stop        # 停止服务
echo    docker-compose restart     # 重启服务
echo    docker-compose down        # 停止并删除容器
echo.
echo 按任意键退出...
pause >nul
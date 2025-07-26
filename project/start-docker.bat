@echo off
chcp 65001 >nul
echo ========================================
echo PMC全流程管理系统 - Docker启动脚本
echo ========================================
echo.

:: 检查Docker是否运行
echo [1/6] 检查Docker服务状态...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行或未安装，请先启动Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker服务正常

:: 检查环境变量文件
echo [2/6] 检查环境配置...
if not exist ".env" (
    echo ⚠️  未找到.env文件，正在复制示例配置...
    copy ".env.example" ".env" >nul
    echo ✅ 已创建.env文件，请根据需要修改配置
) else (
    echo ✅ 环境配置文件存在
)

:: 创建必要的目录
echo [3/6] 创建必要目录...
if not exist "backend\logs" mkdir "backend\logs"
if not exist "backend\uploads" mkdir "backend\uploads"
if not exist "backend\static" mkdir "backend\static"
echo ✅ 目录创建完成

:: 构建镜像
echo [4/6] 构建Docker镜像...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
)
echo ✅ 镜像构建完成

:: 启动服务
echo [5/6] 启动服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)
echo ✅ 服务启动完成

:: 等待服务就绪
echo [6/6] 等待服务就绪...
echo 正在等待数据库初始化...
timeout /t 10 /nobreak >nul

:: 检查服务状态
echo.
echo ========================================
echo 服务状态检查
echo ========================================
docker-compose ps

echo.
echo ========================================
echo 🎉 PMC系统启动完成！
echo ========================================
echo.
echo 📱 访问地址：
echo   - 前端应用: http://localhost:3000
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo   - Nginx代理: http://localhost:80
echo.
echo 🔧 管理命令：
echo   - 查看日志: docker-compose logs -f
echo   - 停止服务: docker-compose down
echo   - 重启服务: docker-compose restart
echo   - 查看状态: docker-compose ps
echo.
echo 👤 默认管理员账号：
echo   - 用户名: admin
echo   - 密码: admin123
echo.
echo ⚠️  首次启动可能需要几分钟时间初始化数据库
echo.
pause
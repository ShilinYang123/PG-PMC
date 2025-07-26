@echo off
chcp 65001 >nul
echo ========================================
echo PMC全流程管理系统 - 开发环境启动脚本
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
echo [2/6] 检查开发环境配置...
if not exist ".env.dev" (
    echo ⚠️  未找到.env.dev文件，正在创建开发环境配置...
    (
        echo # PMC开发环境配置
        echo DB_NAME=pmc_db_dev
        echo DB_PORT=5433
        echo REDIS_PORT=6380
        echo BACKEND_PORT=8001
        echo FRONTEND_PORT=3001
        echo PGADMIN_PORT=5050
        echo REDIS_COMMANDER_PORT=8081
        echo ENVIRONMENT=development
        echo DEBUG=true
        echo LOG_LEVEL=DEBUG
        echo SECRET_KEY=dev-secret-key-not-for-production
    ) > ".env.dev"
    echo ✅ 已创建开发环境配置文件
) else (
    echo ✅ 开发环境配置文件存在
)

:: 创建必要的目录
echo [3/6] 创建必要目录...
if not exist "backend\logs" mkdir "backend\logs"
if not exist "backend\uploads" mkdir "backend\uploads"
if not exist "backend\static" mkdir "backend\static"
echo ✅ 目录创建完成

:: 构建开发镜像
echo [4/6] 构建开发环境Docker镜像...
docker-compose -f docker-compose.dev.yml --env-file .env.dev build
if %errorlevel% neq 0 (
    echo ❌ 开发镜像构建失败
    pause
    exit /b 1
)
echo ✅ 开发镜像构建完成

:: 启动开发服务
echo [5/6] 启动开发环境服务...
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d
if %errorlevel% neq 0 (
    echo ❌ 开发服务启动失败
    pause
    exit /b 1
)
echo ✅ 开发服务启动完成

:: 等待服务就绪
echo [6/6] 等待服务就绪...
echo 正在等待数据库初始化...
timeout /t 15 /nobreak >nul

:: 检查服务状态
echo.
echo ========================================
echo 开发环境服务状态
echo ========================================
docker-compose -f docker-compose.dev.yml ps

echo.
echo ========================================
echo 🚀 PMC开发环境启动完成！
echo ========================================
echo.
echo 📱 开发环境访问地址：
echo   - 前端应用: http://localhost:3001
echo   - 后端API: http://localhost:8001
echo   - API文档: http://localhost:8001/docs
echo   - 数据库管理: http://localhost:5050
echo   - Redis管理: http://localhost:8081
echo.
echo 🔧 开发管理命令：
echo   - 查看日志: docker-compose -f docker-compose.dev.yml logs -f
echo   - 停止服务: docker-compose -f docker-compose.dev.yml down
echo   - 重启服务: docker-compose -f docker-compose.dev.yml restart
echo   - 进入后端: docker exec -it pmc_backend_dev bash
echo   - 进入前端: docker exec -it pmc_frontend_dev sh
echo.
echo 👤 数据库管理员账号：
echo   - 邮箱: admin@pmc.local
echo   - 密码: admin123
echo.
echo 🔄 开发特性：
echo   - 后端热重载: ✅ 已启用
echo   - 前端热重载: ✅ 已启用
echo   - 调试模式: ✅ 已启用
echo   - 详细日志: ✅ 已启用
echo.
echo ⚠️  开发环境首次启动可能需要几分钟时间
echo.
pause
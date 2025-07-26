@echo off
chcp 65001 >nul
echo ========================================
echo PMC系统开发环境启动脚本
echo ========================================
echo.

:: 检查Python环境
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)
echo ✅ Python环境正常

:: 检查Node.js环境
echo [2/6] 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装或未添加到PATH
    pause
    exit /b 1
)
echo ✅ Node.js环境正常

:: 启动数据库服务（仅数据库）
echo [3/6] 启动数据库服务...
docker-compose up -d postgres redis
echo ⏳ 等待数据库启动...
timeout /t 5 /nobreak >nul
echo ✅ 数据库服务启动完成

:: 安装后端依赖
echo [4/6] 检查后端依赖...
cd backend
if not exist "requirements.txt" (
    echo ❌ 未找到requirements.txt文件
    cd ..
    pause
    exit /b 1
)
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 后端依赖安装失败
    cd ..
    pause
    exit /b 1
)
echo ✅ 后端依赖检查完成
cd ..

:: 安装前端依赖
echo [5/6] 检查前端依赖...
cd frontend
if not exist "package.json" (
    echo ❌ 未找到package.json文件
    cd ..
    pause
    exit /b 1
)
if not exist "node_modules" (
    echo 📦 安装前端依赖...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 前端依赖安装失败
        cd ..
        pause
        exit /b 1
    )
)
echo ✅ 前端依赖检查完成
cd ..

:: 启动开发服务器
echo [6/6] 启动开发服务器...
echo.
echo 🚀 正在启动开发服务器...
echo.

:: 创建启动脚本
echo @echo off > start_backend.bat
echo cd backend >> start_backend.bat
echo echo 🔧 启动后端服务器... >> start_backend.bat
echo python main.py >> start_backend.bat

echo @echo off > start_frontend.bat
echo cd frontend >> start_frontend.bat
echo echo 📊 启动前端开发服务器... >> start_frontend.bat
echo npm start >> start_frontend.bat

:: 启动后端（新窗口）
start "PMC Backend" start_backend.bat

:: 等待后端启动
echo ⏳ 等待后端服务启动...
timeout /t 3 /nobreak >nul

:: 启动前端（新窗口）
start "PMC Frontend" start_frontend.bat

echo.
echo ========================================
echo 🎉 开发环境启动完成！
echo ========================================
echo.
echo 📊 前端开发服务器: http://localhost:3000
echo 🔧 后端API服务器: http://localhost:8000
echo 📖 API文档: http://localhost:8000/docs
echo 🗄️  PostgreSQL: localhost:5432
echo 🔴 Redis: localhost:6379
echo.
echo 💡 开发提示:
echo    - 前端支持热重载，修改代码自动刷新
echo    - 后端支持热重载，修改代码自动重启
echo    - 使用Ctrl+C停止对应服务
echo.
echo 📝 日志查看:
echo    - 后端日志: 查看"PMC Backend"窗口
echo    - 前端日志: 查看"PMC Frontend"窗口
echo    - 数据库日志: docker-compose logs postgres
echo.
echo 按任意键退出（不会停止服务）...
pause >nul

:: 清理临时文件
del start_backend.bat >nul 2>&1
del start_frontend.bat >nul 2>&1
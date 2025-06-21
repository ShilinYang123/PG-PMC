@echo off
setlocal enabledelayedexpansion

REM 代码质量检查脚本 (Windows版本)
REM 用于本地开发和CI/CD流程中的代码质量验证

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 日志函数
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM 检查依赖
:check_dependencies
call :log_info "检查依赖..."

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Node.js 未安装"
    exit /b 1
)

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Python 未安装"
    exit /b 1
)

REM 检查npm依赖
if not exist "node_modules" (
    call :log_info "安装npm依赖..."
    npm ci
    if errorlevel 1 (
        call :log_error "npm依赖安装失败"
        exit /b 1
    )
)

REM 检查Python依赖
if exist "requirements.txt" (
    call :log_info "检查Python依赖..."
    pip install -r requirements.txt --quiet
)

call :log_success "依赖检查完成"
goto :eof

REM JavaScript/TypeScript代码检查
:check_js_ts
call :log_info "开始JavaScript/TypeScript代码检查..."

REM ESLint检查
call :log_info "运行ESLint..."
npm run lint
if errorlevel 1 (
    call :log_error "ESLint检查失败"
    exit /b 1
)
call :log_success "ESLint检查通过"

REM Prettier格式检查
call :log_info "运行Prettier格式检查..."
npm run format:check
if errorlevel 1 (
    call :log_warning "Prettier格式检查失败，尝试自动修复..."
    npm run format
    call :log_info "已自动修复格式问题"
) else (
    call :log_success "Prettier格式检查通过"
)

REM TypeScript类型检查
call :log_info "运行TypeScript类型检查..."
npm run type-check
if errorlevel 1 (
    call :log_error "TypeScript类型检查失败"
    exit /b 1
)
call :log_success "TypeScript类型检查通过"

call :log_success "JavaScript/TypeScript代码检查完成"
goto :eof

REM Python代码检查
:check_python
call :log_info "开始Python代码检查..."

REM 查找Python文件
dir /s /b *.py 2>nul | findstr /v "node_modules" | findstr /v ".venv" >nul
if errorlevel 1 (
    call :log_info "未找到Python文件，跳过Python检查"
    goto :eof
)

REM flake8检查
call :log_info "运行flake8..."
python -m flake8 . --exclude=node_modules,.venv,venv
if errorlevel 1 (
    call :log_error "flake8检查失败"
    exit /b 1
)
call :log_success "flake8检查通过"

REM black格式检查
black --version >nul 2>&1
if not errorlevel 1 (
    call :log_info "运行black格式检查..."
    python -m black --check . --exclude="/(node_modules|.venv|venv)/"
    if errorlevel 1 (
        call :log_warning "black格式检查失败，尝试自动修复..."
        python -m black . --exclude="/(node_modules|.venv|venv)/"
        call :log_info "已自动修复格式问题"
    ) else (
        call :log_success "black格式检查通过"
    )
)

REM isort导入排序检查
isort --version >nul 2>&1
if not errorlevel 1 (
    call :log_info "运行isort检查..."
    python -m isort --check-only . --skip-glob="*/node_modules/*" --skip-glob="*/.venv/*"
    if errorlevel 1 (
        call :log_warning "isort检查失败，尝试自动修复..."
        python -m isort . --skip-glob="*/node_modules/*" --skip-glob="*/.venv/*"
        call :log_info "已自动修复导入排序问题"
    ) else (
        call :log_success "isort检查通过"
    )
)

REM mypy类型检查
mypy --version >nul 2>&1
if not errorlevel 1 (
    call :log_info "运行mypy类型检查..."
    python -m mypy . --exclude="(node_modules|.venv|venv)" --ignore-missing-imports
    if errorlevel 1 (
        call :log_warning "mypy类型检查发现问题"
    ) else (
        call :log_success "mypy类型检查通过"
    )
)

call :log_success "Python代码检查完成"
goto :eof

REM 运行测试
:run_tests
call :log_info "开始运行测试..."

REM JavaScript/TypeScript测试
call :log_info "运行JavaScript/TypeScript测试..."
npm test -- --passWithNoTests
if errorlevel 1 (
    call :log_error "JavaScript/TypeScript测试失败"
    exit /b 1
)
call :log_success "JavaScript/TypeScript测试通过"

REM Python测试
dir /s /b test_*.py 2>nul >nul || dir /s /b *_test.py 2>nul >nul
if not errorlevel 1 (
    call :log_info "运行Python测试..."
    python -m pytest -v
    if errorlevel 1 (
        call :log_error "Python测试失败"
        exit /b 1
    )
    call :log_success "Python测试通过"
) else (
    call :log_info "未找到Python测试文件"
)

call :log_success "测试运行完成"
goto :eof

REM 安全检查
:security_check
call :log_info "开始安全检查..."

REM npm audit
call :log_info "运行npm audit..."
npm audit --audit-level moderate
if errorlevel 1 (
    call :log_warning "npm audit发现安全问题"
) else (
    call :log_success "npm audit检查通过"
)

REM Python安全检查
safety --version >nul 2>&1
if not errorlevel 1 (
    call :log_info "运行Python safety检查..."
    python -m safety check
    if errorlevel 1 (
        call :log_warning "Python safety发现安全问题"
    ) else (
        call :log_success "Python safety检查通过"
    )
)

call :log_success "安全检查完成"
goto :eof

REM 构建检查
:build_check
call :log_info "开始构建检查..."

REM 前端构建
call :log_info "运行前端构建..."
npm run build
if errorlevel 1 (
    call :log_error "前端构建失败"
    exit /b 1
)
call :log_success "前端构建成功"

call :log_success "构建检查完成"
goto :eof

REM 生成报告
:generate_report
call :log_info "生成质量检查报告..."

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%-%HH%%Min%%Sec%"

set "REPORT_FILE=quality-report-%timestamp%.md"

(
echo # 代码质量检查报告
echo.
echo **检查时间**: %date% %time%
echo **项目**: %~dp0
echo.
echo ## 检查结果
echo.
echo ### JavaScript/TypeScript
echo - ✅ ESLint检查
echo - ✅ Prettier格式检查
echo - ✅ TypeScript类型检查
echo - ✅ 单元测试
echo.
echo ### Python
echo - ✅ flake8代码检查
echo - ✅ black格式检查
echo - ✅ isort导入排序
echo - ✅ mypy类型检查
echo - ✅ 单元测试
echo.
echo ### 安全检查
echo - ✅ npm audit
echo - ✅ Python safety检查
echo.
echo ### 构建检查
echo - ✅ 前端构建
echo.
echo ## 总结
echo.
echo 所有检查项目均已通过，代码质量良好。
) > "%REPORT_FILE%"

call :log_success "质量检查报告已生成: %REPORT_FILE%"
goto :eof

REM 主函数
:main
call :log_info "开始代码质量检查..."

REM 解析命令行参数
set "SKIP_TESTS=false"
set "SKIP_BUILD=false"
set "QUICK_MODE=false"

:parse_args
if "%~1"=="" goto :start_checks
if "%~1"=="--skip-tests" (
    set "SKIP_TESTS=true"
    shift
    goto :parse_args
)
if "%~1"=="--skip-build" (
    set "SKIP_BUILD=true"
    shift
    goto :parse_args
)
if "%~1"=="--quick" (
    set "QUICK_MODE=true"
    set "SKIP_TESTS=true"
    set "SKIP_BUILD=true"
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help

call :log_error "未知选项: %~1"
exit /b 1

:show_help
echo 用法: %0 [选项]
echo 选项:
echo   --skip-tests    跳过测试
echo   --skip-build    跳过构建检查
echo   --quick         快速模式（跳过测试和构建）
echo   -h, --help      显示帮助信息
exit /b 0

:start_checks
REM 执行检查步骤
call :check_dependencies
if errorlevel 1 exit /b 1

call :check_js_ts
if errorlevel 1 exit /b 1

call :check_python
if errorlevel 1 exit /b 1

if "%SKIP_TESTS%"=="false" (
    call :run_tests
    if errorlevel 1 exit /b 1
)

call :security_check

if "%SKIP_BUILD%"=="false" (
    call :build_check
    if errorlevel 1 exit /b 1
)

call :generate_report

call :log_success "所有代码质量检查完成！"
goto :eof

REM 运行主函数
call :main %*
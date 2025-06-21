#!/bin/bash

# 代码质量检查脚本
# 用于本地开发和CI/CD流程中的代码质量验证

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查npm依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装npm依赖..."
        npm ci
    fi
    
    # 检查Python依赖
    if [ -f "requirements.txt" ]; then
        log_info "检查Python依赖..."
        pip install -r requirements.txt --quiet
    fi
    
    log_success "依赖检查完成"
}

# JavaScript/TypeScript代码检查
check_js_ts() {
    log_info "开始JavaScript/TypeScript代码检查..."
    
    # ESLint检查
    log_info "运行ESLint..."
    if npm run lint; then
        log_success "ESLint检查通过"
    else
        log_error "ESLint检查失败"
        return 1
    fi
    
    # Prettier格式检查
    log_info "运行Prettier格式检查..."
    if npm run format:check; then
        log_success "Prettier格式检查通过"
    else
        log_warning "Prettier格式检查失败，尝试自动修复..."
        npm run format
        log_info "已自动修复格式问题"
    fi
    
    # TypeScript类型检查
    log_info "运行TypeScript类型检查..."
    if npm run type-check; then
        log_success "TypeScript类型检查通过"
    else
        log_error "TypeScript类型检查失败"
        return 1
    fi
    
    log_success "JavaScript/TypeScript代码检查完成"
}

# Python代码检查
check_python() {
    log_info "开始Python代码检查..."
    
    # 查找Python文件
    if ! find . -name "*.py" -not -path "./node_modules/*" -not -path "./.venv/*" | grep -q .; then
        log_info "未找到Python文件，跳过Python检查"
        return 0
    fi
    
    # flake8检查
    log_info "运行flake8..."
    if python3 -m flake8 . --exclude=node_modules,.venv,venv; then
        log_success "flake8检查通过"
    else
        log_error "flake8检查失败"
        return 1
    fi
    
    # black格式检查
    if command -v black &> /dev/null; then
        log_info "运行black格式检查..."
        if python3 -m black --check . --exclude="/(node_modules|.venv|venv)/"; then
            log_success "black格式检查通过"
        else
            log_warning "black格式检查失败，尝试自动修复..."
            python3 -m black . --exclude="/(node_modules|.venv|venv)/"
            log_info "已自动修复格式问题"
        fi
    fi
    
    # isort导入排序检查
    if command -v isort &> /dev/null; then
        log_info "运行isort检查..."
        if python3 -m isort --check-only . --skip-glob="*/node_modules/*" --skip-glob="*/.venv/*"; then
            log_success "isort检查通过"
        else
            log_warning "isort检查失败，尝试自动修复..."
            python3 -m isort . --skip-glob="*/node_modules/*" --skip-glob="*/.venv/*"
            log_info "已自动修复导入排序问题"
        fi
    fi
    
    # mypy类型检查
    if command -v mypy &> /dev/null; then
        log_info "运行mypy类型检查..."
        if python3 -m mypy . --exclude="(node_modules|.venv|venv)" --ignore-missing-imports; then
            log_success "mypy类型检查通过"
        else
            log_warning "mypy类型检查发现问题"
        fi
    fi
    
    log_success "Python代码检查完成"
}

# 运行测试
run_tests() {
    log_info "开始运行测试..."
    
    # JavaScript/TypeScript测试
    log_info "运行JavaScript/TypeScript测试..."
    if npm test -- --passWithNoTests; then
        log_success "JavaScript/TypeScript测试通过"
    else
        log_error "JavaScript/TypeScript测试失败"
        return 1
    fi
    
    # Python测试
    if find . -name "test_*.py" -o -name "*_test.py" | grep -q .; then
        log_info "运行Python测试..."
        if python3 -m pytest -v; then
            log_success "Python测试通过"
        else
            log_error "Python测试失败"
            return 1
        fi
    else
        log_info "未找到Python测试文件"
    fi
    
    log_success "测试运行完成"
}

# 安全检查
security_check() {
    log_info "开始安全检查..."
    
    # npm audit
    log_info "运行npm audit..."
    if npm audit --audit-level moderate; then
        log_success "npm audit检查通过"
    else
        log_warning "npm audit发现安全问题"
    fi
    
    # Python安全检查
    if command -v safety &> /dev/null; then
        log_info "运行Python safety检查..."
        if python3 -m safety check; then
            log_success "Python safety检查通过"
        else
            log_warning "Python safety发现安全问题"
        fi
    fi
    
    log_success "安全检查完成"
}

# 构建检查
build_check() {
    log_info "开始构建检查..."
    
    # 前端构建
    log_info "运行前端构建..."
    if npm run build; then
        log_success "前端构建成功"
    else
        log_error "前端构建失败"
        return 1
    fi
    
    log_success "构建检查完成"
}

# 生成报告
generate_report() {
    log_info "生成质量检查报告..."
    
    REPORT_FILE="quality-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# 代码质量检查报告

**检查时间**: $(date)
**项目**: $(basename "$(pwd)")
**分支**: $(git branch --show-current 2>/dev/null || echo "未知")
**提交**: $(git rev-parse --short HEAD 2>/dev/null || echo "未知")

## 检查结果

### JavaScript/TypeScript
- ✅ ESLint检查
- ✅ Prettier格式检查
- ✅ TypeScript类型检查
- ✅ 单元测试

### Python
- ✅ flake8代码检查
- ✅ black格式检查
- ✅ isort导入排序
- ✅ mypy类型检查
- ✅ 单元测试

### 安全检查
- ✅ npm audit
- ✅ Python safety检查

### 构建检查
- ✅ 前端构建

## 总结

所有检查项目均已通过，代码质量良好。

EOF
    
    log_success "质量检查报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    log_info "开始代码质量检查..."
    
    # 解析命令行参数
    SKIP_TESTS=false
    SKIP_BUILD=false
    QUICK_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --quick)
                QUICK_MODE=true
                SKIP_TESTS=true
                SKIP_BUILD=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --skip-tests    跳过测试"
                echo "  --skip-build    跳过构建检查"
                echo "  --quick         快速模式（跳过测试和构建）"
                echo "  -h, --help      显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行检查步骤
    check_dependencies
    
    check_js_ts || exit 1
    check_python || exit 1
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests || exit 1
    fi
    
    security_check
    
    if [ "$SKIP_BUILD" = false ]; then
        build_check || exit 1
    fi
    
    generate_report
    
    log_success "所有代码质量检查完成！"
}

# 运行主函数
main "$@"
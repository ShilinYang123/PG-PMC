#!/bin/bash

# PinGao AI设计助理 - Python代码质量检查脚本
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
    log_info "检查Python环境和依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv .venv
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 检查pip依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装Python依赖..."
        pip install -r requirements.txt --quiet
    fi
    
    log_success "依赖检查完成"
}

# Python代码检查
check_python() {
    log_info "开始Python代码检查..."
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # Black格式检查
    log_info "运行Black格式检查..."
    if black --check src/ tests/; then
        log_success "Black格式检查通过"
    else
        log_warning "Black格式检查失败，尝试自动修复..."
        black src/ tests/
        log_info "已自动修复格式问题"
    fi
    
    # isort导入排序检查
    log_info "运行isort导入排序检查..."
    if isort --check-only src/ tests/; then
        log_success "isort检查通过"
    else
        log_warning "isort检查失败，尝试自动修复..."
        isort src/ tests/
        log_info "已自动修复导入排序问题"
    fi
    
    # Flake8代码风格检查
    log_info "运行Flake8代码风格检查..."
    if flake8 src/ tests/; then
        log_success "Flake8检查通过"
    else
        log_error "Flake8检查失败"
        return 1
    fi
    
    # MyPy类型检查
    log_info "运行MyPy类型检查..."
    if mypy src/; then
        log_success "MyPy类型检查通过"
    else
        log_error "MyPy类型检查失败"
        return 1
    fi
    
    # Bandit安全检查
    log_info "运行Bandit安全检查..."
    if bandit -r src/; then
        log_success "Bandit安全检查通过"
    else
        log_error "Bandit安全检查失败"
        return 1
    fi
    
    log_success "Python代码检查完成"
}

# 运行测试
run_tests() {
    log_info "开始运行测试..."
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 运行Python测试
    log_info "运行Python单元测试..."
    if python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term; then
        log_success "Python测试通过"
    else
        log_error "Python测试失败"
        return 1
    fi
    
    log_success "所有测试完成"
}

# 生成报告
generate_report() {
    log_info "生成代码质量报告..."
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 生成覆盖率报告
    if [ -f ".coverage" ]; then
        coverage html
        log_success "覆盖率报告已生成: htmlcov/index.html"
    fi
    
    log_success "代码质量报告生成完成"
}

# 主函数
main() {
    log_info "开始代码质量检查流程..."
    
    # 检查依赖
    check_dependencies
    
    # Python代码检查
    check_python
    
    # 运行测试
    run_tests
    
    # 生成报告
    generate_report
    
    log_success "所有代码质量检查完成！"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --skip-tests    跳过测试"
            echo "  --skip-deps     跳过依赖检查"
            echo "  --help          显示帮助信息"
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 运行主函数
main
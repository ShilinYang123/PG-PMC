#!/bin/bash
# 3AI 工作室项目初始化脚本
# 用于快速设置开发环境和项目依赖

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "$1 命令未找到，请先安装 $1"
        exit 1
    fi
}

# 检查Node.js版本
check_node_version() {
    local required_version="18"
    local current_version
    
    if command -v node >/dev/null 2>&1; then
        current_version=$(node -v | sed 's/v//' | cut -d. -f1)
        if [ "$current_version" -ge "$required_version" ]; then
            log_info "✓ Node.js 版本符合要求: $(node -v)"
        else
            log_error "Node.js 版本过低，需要 v${required_version}+ 当前: $(node -v)"
            exit 1
        fi
    else
        log_error "Node.js 未安装"
        exit 1
    fi
}

# 检查Python版本
check_python_version() {
    local required_version="3.8"
    
    if command -v python3 >/dev/null 2>&1; then
        local current_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_info "✓ Python 版本符合要求: $current_version"
        else
            log_error "Python 版本过低，需要 ${required_version}+ 当前: $current_version"
            exit 1
        fi
    else
        log_error "Python3 未安装"
        exit 1
    fi
}

# 安装Node.js依赖
install_node_dependencies() {
    log_step "安装 Node.js 依赖..."
    
    if [ -f "package.json" ]; then
        npm install
        log_info "✓ Node.js 依赖安装完成"
    else
        log_warn "package.json 不存在，跳过 Node.js 依赖安装"
    fi
}

# 创建Python虚拟环境
setup_python_venv() {
    log_step "设置 Python 虚拟环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "✓ Python 虚拟环境创建完成"
    else
        log_info "Python 虚拟环境已存在"
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        log_info "✓ Python 依赖安装完成"
    else
        log_warn "requirements.txt 不存在，跳过 Python 依赖安装"
    fi
}

# 创建环境变量文件
setup_env_file() {
    log_step "设置环境变量文件..."
    
    # 配置文件已整合到 project_config.yaml 中
    log_info "✓ 配置文件使用统一的 project_config.yaml 管理"
}

# 创建必要的目录
setup_directories() {
    log_step "创建必要的目录..."
    
    local dirs=("logs" "uploads" "temp" "dist" "coverage")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "✓ 创建目录: $dir"
        fi
    done
}

# 设置Git钩子
setup_git_hooks() {
    log_step "设置 Git 钩子..."
    
    if [ -d ".git" ]; then
        if command -v npx >/dev/null 2>&1; then
            npx husky install
            log_info "✓ Git 钩子设置完成"
        else
            log_warn "npx 不可用，跳过 Git 钩子设置"
        fi
    else
        log_warn "不是 Git 仓库，跳过 Git 钩子设置"
    fi
}

# 运行初始化测试
run_initial_tests() {
    log_step "运行初始化测试..."
    
    # 类型检查
    if command -v npx >/dev/null 2>&1; then
        npx tsc --noEmit
        log_info "✓ TypeScript 类型检查通过"
    fi
    
    # 代码风格检查
    npm run lint
    log_info "✓ 代码风格检查通过"
    
    # 运行测试
    npm test
    log_info "✓ 测试运行完成"
}

# 显示完成信息
show_completion_info() {
    log_info "🎉 项目初始化完成！"
    echo
    log_info "下一步操作:"
    echo "  1. 编辑 .env 文件设置环境变量"
    echo "  2. 启动开发服务器: npm run dev"
    echo "  3. 访问应用: http://localhost:3000"
    echo "  4. 查看API文档: http://localhost:8000/docs"
    echo
    log_info "有用的命令:"
    echo "  npm run dev          - 启动开发服务器"
    echo "  npm run build        - 构建生产版本"
    echo "  npm run test         - 运行测试"
    echo "  npm run lint         - 代码检查"
    echo "  npm run format       - 代码格式化"
    echo
}

# 主函数
main() {
    log_info "开始初始化 3AI 工作室项目..."
    echo
    
    # 检查系统要求
    check_command "node"
    check_command "npm"
    check_command "python3"
    check_command "pip"
    
    check_node_version
    check_python_version
    
    # 执行初始化步骤
    install_node_dependencies
    setup_python_venv
    setup_env_file
    setup_directories
    setup_git_hooks
    
    # 可选的测试步骤
    if [ "${1:-}" != "--skip-tests" ]; then
        run_initial_tests
    fi
    
    show_completion_info
}

# 执行主函数
main "$@"
#!/bin/bash
# 3AI工作室开发容器后置创建脚本
# 在开发容器创建后自动执行的初始化脚本

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

# 欢迎信息
show_welcome() {
    echo
    echo "🎉 欢迎使用 3AI 工作室开发环境！"
    echo "================================================"
    echo
}

# 设置 Git 配置
setup_git() {
    log_step "配置 Git 设置..."
    
    # 设置安全目录
    git config --global --add safe.directory /workspace
    
    # 设置默认分支名
    git config --global init.defaultBranch main
    
    # 设置推送策略
    git config --global push.default simple
    
    # 设置换行符处理
    git config --global core.autocrlf input
    git config --global core.safecrlf true
    
    log_info "✓ Git 配置完成"
}

# 安装项目依赖
install_dependencies() {
    log_step "安装项目依赖..."
    
    # 检查并安装 Node.js 依赖
    if [ -f "package.json" ]; then
        log_info "安装 Node.js 依赖..."
        npm install
        log_info "✓ Node.js 依赖安装完成"
    else
        log_warn "package.json 不存在，跳过 Node.js 依赖安装"
    fi
    
    # 激活 Python 虚拟环境并安装依赖
    if [ -d "venv" ]; then
        log_info "激活 Python 虚拟环境..."
        source venv/bin/activate
        
        # 升级 pip
        pip install --upgrade pip
        
        # 安装项目依赖
        if [ -f "requirements.txt" ]; then
            log_info "安装 Python 依赖..."
            pip install -r requirements.txt
            log_info "✓ Python 依赖安装完成"
        else
            log_warn "requirements.txt 不存在，跳过 Python 依赖安装"
        fi
        
        # 安装开发依赖
        if [ -f "requirements-dev.txt" ]; then
            log_info "安装 Python 开发依赖..."
            pip install -r requirements-dev.txt
            log_info "✓ Python 开发依赖安装完成"
        fi
    else
        log_warn "Python 虚拟环境不存在，跳过 Python 依赖安装"
    fi
}

# 设置环境变量
setup_environment() {
    log_step "设置环境变量..."
    
    # 配置文件已整合到 project_config.yaml 中
    log_info "✓ 配置文件使用统一的 project_config.yaml 管理"
    
    # 设置 Python 路径
    echo 'export PYTHONPATH=/workspace:$PYTHONPATH' >> ~/.bashrc
    echo 'export PYTHONPATH=/workspace:$PYTHONPATH' >> ~/.zshrc
    
    # 激活虚拟环境的别名
    echo 'alias activate="source /workspace/venv/bin/activate"' >> ~/.bashrc
    echo 'alias activate="source /workspace/venv/bin/activate"' >> ~/.zshrc
    
    log_info "✓ 环境变量设置完成"
}

# 创建必要的目录
setup_directories() {
    log_step "创建项目目录..."
    
    local dirs=("logs" "uploads" "temp" "dist" "coverage" ".vscode")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "✓ 创建目录: $dir"
        fi
    done
}

# 设置 VS Code 配置
setup_vscode() {
    log_step "配置 VS Code 设置..."
    
    # 创建 VS Code 设置目录
    mkdir -p .vscode
    
    # 创建推荐扩展配置
    if [ ! -f ".vscode/extensions.json" ]; then
        cat > .vscode/extensions.json << 'EOF'
{
  "recommendations": [
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-python.python",
    "ms-python.black-formatter",
    "eamodio.gitlens",
    "ms-azuretools.vscode-docker",
    "humao.rest-client",
    "pkief.material-icon-theme"
  ]
}
EOF
        log_info "✓ 创建 VS Code 扩展推荐配置"
    fi
    
    # 创建调试配置
    if [ ! -f ".vscode/launch.json" ]; then
        cat > .vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "启动前端开发服务器",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/node_modules/.bin/vite",
      "args": ["--host", "0.0.0.0"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "env": {
        "NODE_ENV": "development"
      }
    },
    {
      "name": "启动后端API服务器",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
EOF
        log_info "✓ 创建 VS Code 调试配置"
    fi
}

# 设置开发工具
setup_dev_tools() {
    log_step "配置开发工具..."
    
    # 设置 Husky Git 钩子
    if [ -f "package.json" ] && command -v npx >/dev/null 2>&1; then
        npx husky install 2>/dev/null || log_warn "Husky 安装失败，请稍后手动安装"
    fi
    
    # 设置 pre-commit 钩子
    if command -v pre-commit >/dev/null 2>&1 && [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        log_info "✓ pre-commit 钩子安装完成"
    fi
    
    log_info "✓ 开发工具配置完成"
}

# 运行初始化检查
run_health_check() {
    log_step "运行健康检查..."
    
    # 检查 Node.js
    if command -v node >/dev/null 2>&1; then
        log_info "✓ Node.js: $(node --version)"
    else
        log_error "✗ Node.js 未安装"
    fi
    
    # 检查 Python
    if command -v python3 >/dev/null 2>&1; then
        log_info "✓ Python: $(python3 --version)"
    else
        log_error "✗ Python3 未安装"
    fi
    
    # 检查 Git
    if command -v git >/dev/null 2>&1; then
        log_info "✓ Git: $(git --version)"
    else
        log_error "✗ Git 未安装"
    fi
    
    # 检查 Docker
    if command -v docker >/dev/null 2>&1; then
        log_info "✓ Docker CLI 可用"
    else
        log_warn "Docker CLI 不可用"
    fi
}

# 显示完成信息
show_completion() {
    echo
    log_info "🎉 开发环境初始化完成！"
    echo
    log_info "可用的命令:"
    echo "  npm run dev          - 启动开发服务器"
    echo "  npm run build        - 构建生产版本"
    echo "  npm run test         - 运行测试"
    echo "  npm run lint         - 代码检查"
    echo "  activate             - 激活 Python 虚拟环境"
    echo
    log_info "端口映射:"
    echo "  3000  - 前端应用"
    echo "  8000  - 后端 API"
    echo "  5432  - PostgreSQL"
    echo "  6379  - Redis"
    echo "  8025  - MailHog Web UI"
    echo
    log_info "开始愉快的编码吧！ 🚀"
    echo
}

# 主函数
main() {
    show_welcome
    
    setup_git
    install_dependencies
    setup_environment
    setup_directories
    setup_vscode
    setup_dev_tools
    run_health_check
    
    show_completion
}

# 执行主函数
main "$@"
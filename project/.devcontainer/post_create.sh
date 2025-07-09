#!/bin/bash
# PinGao AI设计助理开发容器后置创建脚本
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
    echo "🤖 欢迎使用 PinGao AI设计助理开发环境！"
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
    
    # 创建并激活 Python 虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi
    
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
}

# 设置环境变量
setup_environment() {
    log_step "设置环境变量..."
    
    # 设置 Python 路径
    echo 'export PYTHONPATH=/workspace:$PYTHONPATH' >> ~/.bashrc
    echo 'export PYTHONPATH=/workspace:$PYTHONPATH' >> ~/.zshrc
    
    # 激活虚拟环境的别名
    echo 'alias activate="source /workspace/venv/bin/activate"' >> ~/.bashrc
    echo 'alias activate="source /workspace/venv/bin/activate"' >> ~/.zshrc
    
    # AI开发相关环境变量
    echo 'export CREO_INSTALL_PATH="/opt/creo"' >> ~/.bashrc
    echo 'export CREO_INSTALL_PATH="/opt/creo"' >> ~/.zshrc
    
    log_info "✓ 环境变量设置完成"
}

# 创建必要的目录
setup_directories() {
    log_step "创建项目目录..."
    
    local dirs=("logs" "temp" "models" "data" "outputs" "coverage" ".vscode")
    
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
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.mypy-type-checker",
    "ms-toolsai.jupyter",
    "eamodio.gitlens",
    "github.vscode-pull-request-github",
    "sonarsource.sonarlint-vscode",
    "streetsidesoftware.code-spell-checker",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-markdown",
    "yzhang.markdown-all-in-one",
    "pkief.material-icon-theme",
    "github.github-vscode-theme"
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
      "name": "启动AI设计助理",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "测试Creo集成",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/tests/test_creo_integration.py",
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
    
    # 检查虚拟环境
    if [ -d "venv" ]; then
        log_info "✓ Python 虚拟环境已创建"
    else
        log_warn "Python 虚拟环境未找到"
    fi
}

# 显示完成信息
show_completion() {
    echo
    log_info "🎉 AI设计助理开发环境初始化完成！"
    echo
    log_info "可用的命令:"
    echo "  python src/main.py        - 启动AI设计助理"
    echo "  python -m pytest         - 运行测试"
    echo "  flake8 src/              - 代码检查"
    echo "  black src/               - 代码格式化"
    echo "  activate                 - 激活 Python 虚拟环境"
    echo
    log_info "端口映射:"
    echo "  8000  - AI设计助理服务"
    echo
    log_info "开始AI设计助理开发吧！ 🤖🚀"
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
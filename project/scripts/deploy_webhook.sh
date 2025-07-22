#!/bin/bash

# PMC微信Webhook服务部署脚本
# 用于自动化部署微信API回调处理服务

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

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker/webhook"

# 默认配置
ENVIRONMENT="production"
WITH_NGINX=false
FORCE_REBUILD=false
BACKUP_DATA=true

# 显示帮助信息
show_help() {
    cat << EOF
PMC微信Webhook服务部署脚本

用法: $0 [选项]

选项:
    -e, --env ENVIRONMENT       设置环境 (development|staging|production) [默认: production]
    -n, --with-nginx           启用Nginx反向代理
    -f, --force-rebuild        强制重新构建镜像
    -b, --no-backup           跳过数据备份
    -h, --help                显示此帮助信息

示例:
    $0                         # 使用默认配置部署
    $0 -e development -n       # 开发环境部署并启用Nginx
    $0 -f                      # 强制重新构建并部署

EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--with-nginx)
            WITH_NGINX=true
            shift
            ;;
        -f|--force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        -b|--no-backup)
            BACKUP_DATA=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证环境参数
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "无效的环境: $ENVIRONMENT"
    exit 1
fi

# 检查必要的工具
check_dependencies() {
    log_info "检查依赖工具..."
    
    local missing_tools=()
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
        log_error "请安装Docker和Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 检查环境文件
check_env_file() {
    log_info "检查环境配置文件..."
    
    local env_file="$PROJECT_ROOT/.env"
    if [ ! -f "$env_file" ]; then
        log_error "环境配置文件不存在: $env_file"
        exit 1
    fi
    
    # 检查必要的环境变量
    local required_vars=(
        "WECHAT_CORP_ID"
        "WECHAT_CORP_SECRET"
        "WECHAT_AGENT_ID"
        "MYSQL_USER"
        "MYSQL_PASSWORD"
        "MYSQL_DATABASE"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "环境文件中缺少必要变量: ${missing_vars[*]}"
        exit 1
    fi
    
    log_success "环境配置检查完成"
}

# 备份数据
backup_data() {
    if [ "$BACKUP_DATA" = false ]; then
        log_info "跳过数据备份"
        return
    fi
    
    log_info "备份现有数据..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 备份Docker卷数据
    if docker volume ls | grep -q "webhook_mysql_data"; then
        log_info "备份MySQL数据..."
        docker run --rm -v webhook_mysql_data:/data -v "$backup_dir":/backup alpine tar czf /backup/mysql_data.tar.gz -C /data .
    fi
    
    if docker volume ls | grep -q "webhook_mongodb_data"; then
        log_info "备份MongoDB数据..."
        docker run --rm -v webhook_mongodb_data:/data -v "$backup_dir":/backup alpine tar czf /backup/mongodb_data.tar.gz -C /data .
    fi
    
    if docker volume ls | grep -q "webhook_redis_data"; then
        log_info "备份Redis数据..."
        docker run --rm -v webhook_redis_data:/data -v "$backup_dir":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    fi
    
    log_success "数据备份完成: $backup_dir"
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."
    
    cd "$DOCKER_DIR"
    
    if [ "$WITH_NGINX" = true ]; then
        docker-compose --profile with-nginx down
    else
        docker-compose down
    fi
    
    log_success "服务已停止"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    cd "$DOCKER_DIR"
    
    local build_args=()
    if [ "$FORCE_REBUILD" = true ]; then
        build_args+=("--no-cache")
    fi
    
    docker-compose build "${build_args[@]}"
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd "$DOCKER_DIR"
    
    # 设置环境变量
    export COMPOSE_PROJECT_NAME="pmc-webhook-$ENVIRONMENT"
    
    if [ "$WITH_NGINX" = true ]; then
        docker-compose --profile with-nginx up -d
    else
        docker-compose up -d
    fi
    
    log_success "服务已启动"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "服务已就绪"
            return 0
        fi
        
        log_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "服务启动超时"
    return 1
}

# 运行健康检查
run_health_check() {
    log_info "运行健康检查..."
    
    # 检查webhook服务
    if ! curl -f http://localhost:8080/health; then
        log_error "Webhook服务健康检查失败"
        return 1
    fi
    
    # 检查API状态
    if ! curl -f http://localhost:8080/api/v1/status; then
        log_error "API状态检查失败"
        return 1
    fi
    
    log_success "健康检查通过"
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成!"
    
    echo
    echo "服务信息:"
    echo "  环境: $ENVIRONMENT"
    echo "  Webhook服务: http://localhost:8080"
    echo "  健康检查: http://localhost:8080/health"
    echo "  API状态: http://localhost:8080/api/v1/status"
    
    if [ "$WITH_NGINX" = true ]; then
        echo "  Nginx代理: http://localhost (HTTP) / https://localhost (HTTPS)"
    fi
    
    echo
    echo "有用的命令:"
    echo "  查看日志: docker-compose -f $DOCKER_DIR/docker-compose.yml logs -f"
    echo "  停止服务: docker-compose -f $DOCKER_DIR/docker-compose.yml down"
    echo "  重启服务: docker-compose -f $DOCKER_DIR/docker-compose.yml restart"
    echo
}

# 主函数
main() {
    log_info "开始部署PMC微信Webhook服务 (环境: $ENVIRONMENT)"
    
    check_dependencies
    check_env_file
    backup_data
    stop_services
    build_images
    start_services
    
    if wait_for_services && run_health_check; then
        show_deployment_info
    else
        log_error "部署失败，请检查日志"
        exit 1
    fi
}

# 捕获中断信号
trap 'log_error "部署被中断"; exit 1' INT TERM

# 运行主函数
main
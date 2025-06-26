#!/bin/bash
# 3AI 工作室项目健康检查脚本
# 用于检查应用程序和依赖服务的运行状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 加载统一配置
load_config() {
    local config_dir="$(dirname "$(dirname "$(dirname "$(realpath "$0")")")")")/docs/03-管理"
    
    if [ -f "$config_dir/.env" ]; then
        source "$config_dir/.env"
        log_info "已加载统一配置: $config_dir/.env"
    else
        log_warn "未找到统一配置文件，使用默认值"
        # 设置默认值
        PORT=${PORT:-3000}
        API_PORT=${API_PORT:-8000}
        DB_HOST=${DB_HOST:-127.0.0.1}
        DB_PORT=${DB_PORT:-5432}
        REDIS_HOST=${REDIS_HOST:-127.0.0.1}
        REDIS_PORT=${REDIS_PORT:-6379}
        PROJECT_NAME=${PROJECT_NAME:-3AI}
    fi
}

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

# 检查HTTP服务
check_http_service() {
    local url=$1
    local service_name=$2
    
    log_info "检查 $service_name 服务: $url"
    
    if curl -f -s --max-time 10 "$url" > /dev/null; then
        log_info "✓ $service_name 服务正常"
        return 0
    else
        log_error "✗ $service_name 服务异常"
        return 1
    fi
}

# 检查端口
check_port() {
    local host=$1
    local port=$2
    local service_name=$3
    
    log_info "检查 $service_name 端口: $host:$port"
    
    if nc -z "$host" "$port" 2>/dev/null; then
        log_info "✓ $service_name 端口可达"
        return 0
    else
        log_error "✗ $service_name 端口不可达"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    local db_url=${DATABASE_URL:-"postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-password}@${DB_HOST}:${DB_PORT}/${DB_NAME:-${PROJECT_NAME}_db}"}
    
    log_info "检查数据库连接: ${DB_HOST}:${DB_PORT}"
    
    if command -v psql >/dev/null 2>&1; then
        if psql "$db_url" -c "SELECT 1;" >/dev/null 2>&1; then
            log_info "✓ 数据库连接正常"
            return 0
        else
            log_error "✗ 数据库连接失败"
            return 1
        fi
    else
        log_warn "psql 命令不可用，跳过数据库检查"
        return 0
    fi
}

# 检查Redis连接
check_redis() {
    local redis_url=${REDIS_URL:-"redis://${REDIS_HOST}:${REDIS_PORT}/0"}
    
    log_info "检查Redis连接: ${REDIS_HOST}:${REDIS_PORT}"
    
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null 2>&1; then
            log_info "✓ Redis连接正常"
            return 0
        else
            log_error "✗ Redis连接失败"
            return 1
        fi
    else
        log_warn "redis-cli 命令不可用，跳过Redis检查"
        return 0
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间"
    
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt 80 ]; then
        log_info "✓ 磁盘空间充足 (${usage}% 已使用)"
        return 0
    elif [ "$usage" -lt 90 ]; then
        log_warn "⚠ 磁盘空间不足 (${usage}% 已使用)"
        return 0
    else
        log_error "✗ 磁盘空间严重不足 (${usage}% 已使用)"
        return 1
    fi
}

# 检查内存使用
check_memory() {
    log_info "检查内存使用"
    
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$mem_usage" -lt 80 ]; then
        log_info "✓ 内存使用正常 (${mem_usage}% 已使用)"
        return 0
    elif [ "$mem_usage" -lt 90 ]; then
        log_warn "⚠ 内存使用较高 (${mem_usage}% 已使用)"
        return 0
    else
        log_error "✗ 内存使用过高 (${mem_usage}% 已使用)"
        return 1
    fi
}

# 主检查函数
main() {
    # 加载配置
    load_config
    
    log_info "开始3AI工作室项目健康检查..."
    
    local exit_code=0
    
    # 基础系统检查
    check_disk_space || exit_code=1
    check_memory || exit_code=1
    
    # 服务检查
    check_http_service "http://${DB_HOST}:${API_PORT}/health" "后端API" || exit_code=1
    check_http_service "http://${DB_HOST}:${PORT}" "前端应用" || exit_code=1

    # 数据库检查
    check_database || exit_code=1
    check_redis || exit_code=1

    # 端口检查
    check_port "${DB_HOST}" "${API_PORT}" "后端服务" || exit_code=1
    check_port "${DB_HOST}" "${PORT}" "前端服务" || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        log_info "🎉 所有检查通过，系统运行正常！"
    else
        log_error "❌ 发现问题，请检查上述错误信息"
    fi
    
    exit $exit_code
}

# 执行主函数
main "$@"
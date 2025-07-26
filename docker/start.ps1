# Docker快速启动脚本
# 用于快速启动PMC项目的Docker环境

Write-Host "=== PMC项目Docker启动脚本 ===" -ForegroundColor Green

# 检查Docker是否运行
Write-Host "检查Docker状态..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker运行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 停止现有容器
Write-Host "停止现有容器..." -ForegroundColor Yellow
docker-compose down

# 构建镜像
Write-Host "构建Docker镜像..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 镜像构建失败" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "启动服务..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 服务启动成功" -ForegroundColor Green
    Write-Host ""
    Write-Host "服务访问地址:" -ForegroundColor Cyan
    Write-Host "  生产环境: http://localhost:8000" -ForegroundColor White
    Write-Host "  开发环境: http://localhost:8001" -ForegroundColor White
    Write-Host ""
    Write-Host "常用命令:" -ForegroundColor Cyan
    Write-Host "  查看日志: cd docker && docker-compose logs -f" -ForegroundColor White
    Write-Host "  停止服务: cd docker && docker-compose down" -ForegroundColor White
    Write-Host "  重启服务: cd docker && docker-compose restart" -ForegroundColor White
    Write-Host "  进入容器: docker exec -it pmc-development bash" -ForegroundColor White
} else {
    Write-Host "❌ 服务启动失败" -ForegroundColor Red
    Write-Host "查看错误日志: docker-compose logs" -ForegroundColor Yellow
    exit 1
}
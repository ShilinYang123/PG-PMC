# PMC项目Docker启动脚本
# 从根目录启动Docker环境，支持快速启动和完整构建

param(
    [switch]$Quick,  # 快速启动，跳过构建检查
    [switch]$Force   # 强制重新构建
)

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

# 切换到docker目录
Write-Host "正在切换到docker目录..." -ForegroundColor Yellow
Set-Location -Path "docker"

if ($Quick) {
    Write-Host "🚀 快速启动模式" -ForegroundColor Cyan
    
    # 检查镜像是否存在
    $images = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -match "pmc-" }
    if ($images.Count -eq 0) {
        Write-Host "❌ 未找到PMC镜像，切换到完整构建模式" -ForegroundColor Yellow
        .\start.ps1
    } else {
        Write-Host "✅ 发现现有镜像，直接启动服务" -ForegroundColor Green
        
        # 停止现有容器
        Write-Host "停止现有容器..." -ForegroundColor Yellow
        docker-compose down
        
        # 直接启动服务
        Write-Host "启动服务..." -ForegroundColor Yellow
        docker-compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 服务启动成功" -ForegroundColor Green
            Write-Host ""
            Write-Host "服务访问地址:" -ForegroundColor Cyan
            Write-Host "  生产环境: http://localhost:8000" -ForegroundColor White
            Write-Host "  开发环境: http://localhost:8001" -ForegroundColor White
            Write-Host "  监控面板: http://localhost:8002" -ForegroundColor White
        } else {
            Write-Host "❌ 服务启动失败" -ForegroundColor Red
            Write-Host "查看错误日志: docker-compose logs" -ForegroundColor Yellow
        }
    }
} elseif ($Force) {
    Write-Host "🔨 强制重建模式" -ForegroundColor Cyan
    Write-Host "停止并删除所有容器..." -ForegroundColor Yellow
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
} else {
    Write-Host "🔍 智能检查模式" -ForegroundColor Cyan
    # 执行docker目录中的启动脚本（带智能缓存检查）
    .\start.ps1
}

# 返回根目录
Set-Location -Path ".."

Write-Host ""
Write-Host "💡 使用提示:" -ForegroundColor Cyan
Write-Host "  快速启动: .\tools\docker-start.ps1 -Quick" -ForegroundColor White
Write-Host "  强制重建: .\tools\docker-start.ps1 -Force" -ForegroundColor White
Write-Host "  智能检查: .\tools\docker-start.ps1" -ForegroundColor White
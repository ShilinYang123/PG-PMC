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

# 检查是否需要构建镜像
Write-Host "检查镜像状态..." -ForegroundColor Yellow
$needBuild = $false

# 检查镜像是否存在
$images = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -match "pmc-" }
if ($images.Count -eq 0) {
    Write-Host "未找到PMC镜像，需要构建" -ForegroundColor Yellow
    $needBuild = $true
} else {
    Write-Host "发现现有镜像，检查是否需要更新..." -ForegroundColor Yellow
    # 检查Dockerfile和docker-compose.yml的修改时间
    $dockerfileTime = (Get-Item "Dockerfile").LastWriteTime
    $composeTime = (Get-Item "docker-compose.yml").LastWriteTime
    $requirementsTime = (Get-Item "requirements.txt").LastWriteTime
    
    # 获取最新的镜像创建时间
    $imageTime = docker inspect --format='{{.Created}}' (docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -match "pmc-" } | Select-Object -First 1)
    if ($imageTime) {
        $imageCreated = [DateTime]::Parse($imageTime)
        if ($dockerfileTime -gt $imageCreated -or $composeTime -gt $imageCreated -or $requirementsTime -gt $imageCreated) {
            Write-Host "配置文件已更新，需要重新构建" -ForegroundColor Yellow
            $needBuild = $true
        }
    }
}

if ($needBuild) {
    Write-Host "构建Docker镜像..." -ForegroundColor Yellow
    docker-compose build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 镜像构建失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 镜像构建完成" -ForegroundColor Green
} else {
    Write-Host "✅ 使用现有镜像，跳过构建" -ForegroundColor Green
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
    Write-Host "  查看日志: docker-compose logs -f" -ForegroundColor White
    Write-Host "  停止服务: docker-compose down" -ForegroundColor White
    Write-Host "  重启服务: docker-compose restart" -ForegroundColor White
    Write-Host "  强制重建: docker-compose build --no-cache" -ForegroundColor White
    Write-Host "  进入容器: docker exec -it pmc-development bash" -ForegroundColor White
} else {
    Write-Host "❌ 服务启动失败" -ForegroundColor Red
    Write-Host "查看错误日志: docker-compose logs" -ForegroundColor Yellow
    exit 1
}
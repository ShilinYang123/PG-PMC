# PMC项目Docker快速启动脚本
# 从根目录启动Docker环境

Write-Host "=== PMC项目Docker启动脚本 ===" -ForegroundColor Green
Write-Host "正在切换到docker目录..." -ForegroundColor Yellow

# 切换到docker目录
Set-Location -Path "docker"

# 执行docker目录中的启动脚本
.\start.ps1

# 返回根目录
Set-Location -Path ".."
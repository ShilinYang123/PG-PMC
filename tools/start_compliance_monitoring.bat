@echo off
echo 启动项目合规性监控系统...
cd /d "s:\PG-Dev"
python "s:\PG-Dev\tools\compliance_monitor.py" --start
pause

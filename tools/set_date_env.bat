@echo off
REM 设置系统日期环境变量
REM 创建时间: 2025年07月26日

echo 正在设置系统日期环境变量...

REM 运行Python脚本获取当前日期并设置环境变量
python -c "
import os
from datetime import datetime

now = datetime.now()

# 设置环境变量
date_vars = {
    'SYSTEM_CURRENT_DATE': now.strftime('%%Y-%%m-%%d'),
    'SYSTEM_CURRENT_DATETIME': now.strftime('%%Y-%%m-%%d %%H:%%M:%%S'),
    'SYSTEM_CURRENT_DATE_FORMATTED': now.strftime('%%Y年%%m月%%d日'),
    'SYSTEM_CURRENT_YEAR': str(now.year),
    'SYSTEM_CURRENT_MONTH': str(now.month),
    'SYSTEM_CURRENT_DAY': str(now.day),
    'SYSTEM_CURRENT_WEEKDAY': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()],
    'SYSTEM_TIMESTAMP': now.isoformat()
}

# 生成批处理命令
with open('temp_set_env.bat', 'w', encoding='gbk') as f:
    f.write('@echo off\n')
    for var_name, value in date_vars.items():
        f.write(f'set {var_name}={value}\n')
    f.write('echo 环境变量设置完成！\n')
    f.write('echo 当前日期: %%SYSTEM_CURRENT_DATE_FORMATTED%%\n')
"

REM 执行生成的批处理文件
if exist temp_set_env.bat (
    call temp_set_env.bat
    del temp_set_env.bat
) else (
    echo 生成环境变量设置文件失败
)

echo.
echo 使用方法:
echo   在PowerShell中: $env:SYSTEM_CURRENT_DATE_FORMATTED
echo   在CMD中: %%SYSTEM_CURRENT_DATE_FORMATTED%%
echo.
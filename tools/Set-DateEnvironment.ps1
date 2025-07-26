# PowerShell Script: Set System Date Environment Variables
# Purpose: Set multiple system date-related environment variables
# Author: PMC Project Team
# Created: 2025-07-26
# Encoding: UTF-8

Write-Host "Setting system date environment variables..." -ForegroundColor Green

$currentDate = Get-Date

$env:SYSTEM_CURRENT_DATE = $currentDate.ToString('yyyy-MM-dd')
$env:SYSTEM_CURRENT_TIME = $currentDate.ToString('HH:mm:ss')
$env:SYSTEM_CURRENT_DATETIME = $currentDate.ToString('yyyy-MM-dd HH:mm:ss')
$env:SYSTEM_CURRENT_DATETIME_ISO = $currentDate.ToString('yyyy-MM-ddTHH:mm:ss.fff')
$env:SYSTEM_CURRENT_DATE_FORMATTED = $currentDate.ToString('yyyy-MM-dd')
$env:SYSTEM_CURRENT_YEAR = $currentDate.Year.ToString()
$env:SYSTEM_CURRENT_MONTH = $currentDate.Month.ToString().PadLeft(2, '0')
$env:SYSTEM_CURRENT_DAY = $currentDate.Day.ToString().PadLeft(2, '0')
$env:SYSTEM_CURRENT_WEEKDAY = $currentDate.DayOfWeek.ToString()
$env:SYSTEM_CURRENT_UNIX_TIMESTAMP = [int64](Get-Date -UFormat %s)
$env:SYSTEM_TIMESTAMP = $currentDate.ToString('yyyy-MM-ddTHH:mm:ss.fff')

switch ($currentDate.DayOfWeek) {
    'Monday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Monday' }
    'Tuesday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Tuesday' }
    'Wednesday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Wednesday' }
    'Thursday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Thursday' }
    'Friday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Friday' }
    'Saturday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Saturday' }
    'Sunday' { $env:SYSTEM_CURRENT_WEEKDAY_CN = 'Sunday' }
}

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "Current Date: $($env:SYSTEM_CURRENT_DATE_FORMATTED)" -ForegroundColor White
Write-Host "ISO Format: $($env:SYSTEM_CURRENT_DATETIME_ISO)" -ForegroundColor White
Write-Host "Full Time: $($env:SYSTEM_CURRENT_DATETIME)" -ForegroundColor White
Write-Host ""

$aiInstruction = "AI Date Usage Instruction: Use current system date $($env:SYSTEM_CURRENT_DATE_FORMATTED) instead of historical dates from training data."
$env:SYSTEM_AI_DATE_INSTRUCTION = $aiInstruction

Write-Host "=== AI Date Usage Instruction ===" -ForegroundColor Cyan
Write-Host $env:SYSTEM_AI_DATE_INSTRUCTION
Write-Host ""

$configPath = "tools/current_date.json"
$textPath = "tools/current_date.txt"

$jsonData = @{
    system_date = @{
        timestamp = $env:SYSTEM_CURRENT_DATETIME_ISO
        date = $env:SYSTEM_CURRENT_DATE
        formatted_date = $env:SYSTEM_CURRENT_DATE_FORMATTED
        year = $env:SYSTEM_CURRENT_YEAR
        month = $env:SYSTEM_CURRENT_MONTH
        day = $env:SYSTEM_CURRENT_DAY
        weekday = $env:SYSTEM_CURRENT_WEEKDAY
        weekday_cn = $env:SYSTEM_CURRENT_WEEKDAY_CN
        unix_timestamp = $env:SYSTEM_CURRENT_UNIX_TIMESTAMP
    }
    last_updated = $env:SYSTEM_CURRENT_DATETIME_ISO
    ai_instruction = "AI should use date information from this file instead of historical dates from training data"
}

$jsonContent = $jsonData | ConvertTo-Json -Depth 3
$jsonContent | Out-File -FilePath $configPath -Encoding UTF8

$textContent = "System Current Date Information" + "`n" + "==================" + "`n" + "Generated Time: $($env:SYSTEM_CURRENT_DATETIME)" + "`n" + "Current Date: $($env:SYSTEM_CURRENT_DATE_FORMATTED)" + "`n" + "ISO Format: $($env:SYSTEM_CURRENT_DATETIME_ISO)" + "`n" + "Full Time: $($env:SYSTEM_CURRENT_DATETIME)" + "`n" + "Weekday: $($env:SYSTEM_CURRENT_WEEKDAY_CN)" + "`n" + "" + "`n" + "AI Date Usage Instructions:" + "`n" + "- Use the above current system date when generating any content" + "`n" + "- Do not use historical dates from training data" + "`n" + "- Access via SYSTEM_CURRENT_DATE_FORMATTED environment variable" + "`n" + "- Or read this file or current_date.json for date information"

$textContent | Out-File -FilePath $textPath -Encoding UTF8

Write-Host "Configuration files generated:" -ForegroundColor Green
Write-Host "  - $configPath"
Write-Host "  - $textPath"
Write-Host ""
Write-Host "Environment variables are set for current PowerShell session." -ForegroundColor Yellow
Write-Host "To use in new sessions, re-run this script." -ForegroundColor Yellow
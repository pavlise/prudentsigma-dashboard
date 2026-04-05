# Setup Windows Task Scheduler for daily report generation
$taskName = "PrudentSigma Daily Market Report"
$scriptPath = "C:\Users\Pavlos Elpidorou\Documents\AI_Project\daily_market_report\scheduler\generate_daily_report.bat"
$workingDir = "C:\Users\Pavlos Elpidorou\Documents\AI_Project"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing it first..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create new scheduled task
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Daily -At 6AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Generates daily PrudentSigma market report at 6 AM"

Write-Host "Scheduled task '$taskName' created successfully."
Write-Host "The task will run daily at 6:00 AM."
Write-Host "To view/edit the task, open Task Scheduler and look for '$taskName'."
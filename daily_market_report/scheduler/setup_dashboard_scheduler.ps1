# Setup Windows Task Scheduler for Streamlit Dashboard
$taskName = "PrudentSigma Dashboard"
$scriptPath = "C:\Users\Pavlos Elpidorou\Documents\AI_Project\daily_market_report\scheduler\start_dashboard.bat"
$workingDir = "C:\Users\Pavlos Elpidorou\Documents\AI_Project"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing it first..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create new scheduled task for dashboard
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Daily -At 5:55AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Starts PrudentSigma Streamlit Dashboard daily at 5:55 AM"

Write-Host "Scheduled task '$taskName' created successfully."
Write-Host ""
Write-Host "Dashboard Schedule:"
Write-Host "  - Runs daily at 5:55 AM"
Write-Host "  - Available at: http://localhost:8501"
Write-Host "  - Network URL: http://192.168.10.15:8501"
Write-Host ""
Write-Host "Reports Schedule:"
Write-Host "  - Generated daily at 6:00 AM"
Write-Host "  - Accessible via the dashboard"
Write-Host ""
Write-Host "To view/edit the task, open Task Scheduler and search for '$taskName'."

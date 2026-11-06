# Registers an hourly task that works through the Voyage free-tier embedding backlog (see embed-job.cmd).
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\schedule-embedding.ps1        (add -Remove to unregister)
param([switch]$Remove)
$name = "SpectrumKG-Embed"
if ($Remove) { Unregister-ScheduledTask -TaskName $name -Confirm:$false; return }
$job = Join-Path $PSScriptRoot "embed-job.cmd"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command & `'$job`'"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Force `
    -Description "Embeds the SpectrumERP knowledge graph with Voyage AI within free-tier limits; removes itself when done." | Out-Null
Write-Host "Registered '$name': hourly, first run in 1 minute. Log: $(Join-Path (Split-Path $PSScriptRoot) '.cache\embed-job.log')"

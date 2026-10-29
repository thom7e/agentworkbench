# Registers the agentworkbench:// link handler for the current user (no admin rights needed).
$python = (Get-Command pythonw.exe).Source
$script = Join-Path $PSScriptRoot 'awb_run.py'
$key = 'HKCU:\Software\Classes\agentworkbench'
New-Item -Path "$key\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path $key -Name '(default)' -Value 'URL:AgentWorkbench'
Set-ItemProperty -Path $key -Name 'URL Protocol' -Value ''
Set-ItemProperty -Path "$key\shell\open\command" -Name '(default)' -Value "`"$python`" `"$script`" `"%1`""
Write-Host "Registered agentworkbench:// -> $script"

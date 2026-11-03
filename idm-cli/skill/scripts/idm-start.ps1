# Start one file in Internet Download Manager and prove it started.
# Usage (from PowerShell, never from Git Bash):
#   & "<skills dir>\download-big-files-with-idm\scripts\idm-start.ps1" -Url <url> -Dir <folder> -Name <file> [-ExpectedBytes <n>]
# idm.exe is looked up on PATH, then in $env:IDM_CLI (full path of idm.exe).
param(
  [Parameter(Mandatory)] [string] $Url,
  [Parameter(Mandatory)] [string] $Dir,
  [Parameter(Mandatory)] [string] $Name,
  [long] $ExpectedBytes = 0,
  [switch] $NoHide
)

$idm = if ($env:IDM_EXE) { $env:IDM_EXE } else { 'C:\Program Files (x86)\Internet Download Manager\IDMan.exe' }
if (-not (Test-Path $idm)) { throw "IDMan.exe not found at $idm (set IDM_EXE to its path)" }
New-Item -ItemType Directory -Force $Dir | Out-Null

# Each argument is quoted by hand: Start-Process joins the array with spaces,
# and signed CDN URLs carry & and = that must stay inside one argument.
# One command, under a second: idm.exe add starts the download with IDM's command line and hides the
# new progress window at once (SW_HIDE, the same as IDM's "hide beside the clock"; the download continues).
# IDM's main window never opens. Source: src/idm.cs in the agent-tools repo.
$hidden = $false
if ($NoHide) {
  Start-Process $idm -ArgumentList @('/d', "`"$Url`"", '/p', "`"$Dir`"", '/f', "`"$Name`"", '/n'); Start-Sleep 8
} else {
  $cli = (Get-Command idm.exe -ErrorAction SilentlyContinue).Source
  if (-not $cli -and $env:IDM_CLI) { $cli = $env:IDM_CLI }
  if (-not $cli) { throw 'idm.exe not found: put it on PATH or set IDM_CLI to its full path' }
  $out = & $cli add $Url $Dir $Name
  $out | ForEach-Object { Write-Host $_ }
  $hidden = [bool]($out -match 'progress window hidden')
}

$running = Get-CimInstance Win32_Process -Filter "Name='IDMan.exe'" | Select-Object -First 1
$target = Join-Path $Dir $Name

[pscustomobject]@{
  IdmRunning      = [bool]$running
  ProgressHidden  = $hidden
  FileExistsYet   = Test-Path $target
  Bytes           = if (Test-Path $target) { (Get-Item $target).Length } else { 0 }
  ExpectedBytes   = $ExpectedBytes
} | Format-List

# IdmRunning only proves the process is up, not that bytes move.
# Confirm the transfer with idm-status.ps1 (two looks, the byte count must rise) before telling anyone it is downloading.

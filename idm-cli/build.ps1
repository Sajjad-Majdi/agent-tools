# Builds idm.exe from src\idm.cs with the C# compiler that ships with Windows (.NET Framework 4). No SDK needed.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 [-Out <folder>]
param([string]$Out = (Join-Path $PSScriptRoot 'bin'))
$fw = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319"
$csc = Join-Path $fw 'csc.exe'
if (-not (Test-Path $csc)) { throw "csc.exe not found at $csc" }
New-Item -ItemType Directory -Force $Out | Out-Null
$exe = Join-Path (Resolve-Path $Out) 'idm.exe'
& $csc -nologo -optimize "-out:$exe" `
  "-r:$fw\WPF\UIAutomationClient.dll" "-r:$fw\WPF\UIAutomationTypes.dll" "-r:$fw\WPF\WindowsBase.dll" `
  -r:System.Windows.Forms.dll -r:System.Core.dll (Join-Path $PSScriptRoot 'src\idm.cs')
if ($LASTEXITCODE -ne 0) { throw 'build failed' }
Write-Output "built $exe"

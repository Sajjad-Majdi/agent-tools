# Read IDM download status straight from IDM's own state. No screenshots, no UI.
# Usage (PowerShell):
#   & "<skills dir>\download-big-files-with-idm\scripts\idm-status.ps1"                         # last 5 items
#   & "...\idm-status.ps1" -Match model.fp16.onnx                                                # filter by name/url/folder
#   & "...\idm-status.ps1" -Match model.fp16.onnx -Wait                                          # block until done or stopped
# Source of truth:
#   HKCU:\Software\DownloadManager\<id>  FileSize / Downloaded / Speed = little-endian 8-byte ints,
#                                         Status 1 = running, 2 = stopped/finished, lastResult = IDM's message.
#   %APPDATA%\IDM\DwnlData\<user>\<host>_<id>\  part files; their sum is the live byte count
#                                         (the registry only refreshes every few seconds).
#   The finished file appears in LocalPath\LocalFileName only at the very end.
param([string] $Match = '', [int] $Last = 0, [switch] $Wait, [int] $Every = 15)
# -Last 0 = all matching items when -Match is given, else the last 5 (a fixed 5 would hide older items).
if ($Last -le 0) { $Last = if ($Match) { 10000 } else { 5 } }

$root = 'HKCU:\Software\DownloadManager'
function U64($b) { if ($b -is [byte[]] -and $b.Length -ge 8) { [BitConverter]::ToUInt64($b, 0) } elseif ($b) { [uint64]$b } else { 0 } }
function Fix($s) {  # IDM stores Persian text as Windows-1256 bytes read as Windows-1252
  if (-not $s) { return '' }
  try { [Text.Encoding]::GetEncoding(1256).GetString([Text.Encoding]::GetEncoding(1252).GetBytes($s)) } catch { $s }
}

function Get-Items {
  Get-ChildItem $root | Where-Object { $_.PSChildName -match '^\d+$' } | ForEach-Object {
    $p = Get-ItemProperty $_.PSPath
    if (-not $p.Url0) { return }
    $id = $_.PSChildName
    $name = $p.LocalFileName
    if ($p.Url0 -match "filename%3D%22([^%]+)%22") { $remote = $Matches[1] } else { $remote = ($p.FileName -split '\?')[0] }
    $size = U64 $p.FileSize
    $done = U64 $p.Downloaded
    $tmp = $p.LocalPath
    $live = 0
    if ($tmp -and (Test-Path $tmp) -and $tmp -like '*\IDM\DwnlData\*') {
      # live bytes from the item log (dir-listing sizes freeze while IDM holds files open)
      $lg = Get-ChildItem $tmp -Filter '*.log' -File | Select-Object -First 1
      $ln = if ($lg) { Get-Content $lg.FullName -Tail 50 | Where-Object { $_ -match 'downl (\d+) Bytes' } | Select-Object -Last 1 }
      if ($ln -match 'time (\d+), speed (\d+), downl (\d+) Bytes') {
        $live = [double]$Matches[3]
        if (([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - [long]$Matches[1]) -lt 60) { $p.Status = 1; $p.Speed = [uint64]$Matches[2] }
      }
    }
    $bytes = [math]::Max([double]$done, [double]$live)
    $speed = U64 $p.Speed
    [pscustomobject]@{
      Id      = [int]$id
      Name    = if ($name -and $name -notlike '*\DwnlData\*') { Split-Path $name -Leaf } else { $remote }
      Target  = if ($name -and $name -notlike '*\DwnlData\*') { $name } else { '' }
      State   = switch ($p.Status) { 1 { 'running' } 0 { 'queued' } 2 { if ($size -and $bytes -ge $size) { 'done' } else { 'stopped' } } 3 { 'done' } default { "status $($p.Status)" } }
      Percent = if ($size) { [math]::Round(100 * $bytes / $size, 1) } else { $null }
      MB      = '{0:N1} / {1:N1}' -f ($bytes / 1MB), ($size / 1MB)
      Speed   = if ($p.Status -eq 1) { '{0:N2} MB/s' -f ($speed / 1MB) } else { '' }
      ETA     = if ($p.Status -eq 1 -and $speed -gt 0 -and $size) { [TimeSpan]::FromSeconds([int](($size - $bytes) / $speed)).ToString() } else { '' }
      Message = Fix $p.lastResult
      Url     = $p.Url0
    }
  } | Where-Object { -not $Match -or $_.Name -like "*$Match*" -or $_.Target -like "*$Match*" -or $_.Url -like "*$Match*" } |
      Sort-Object Id | Select-Object -Last $Last
}

do {
  $items = @(Get-Items)
  $items | Select-Object Id, Name, State, Percent, MB, Speed, ETA, Message | Format-Table -AutoSize | Out-String -Width 200 | Write-Output
  $busy = $items | Where-Object State -eq 'running'
  if ($Wait -and $busy) { Start-Sleep $Every }
} while ($Wait -and $busy)

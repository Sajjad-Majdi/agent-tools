# Render a DOCX to PDF through Microsoft Word without saving the DOCX.
# Word strips explicit RTL direct formatting on save, so the source file is left untouched.
# Pass the directory holding the DOCX; the newest matching file is used.
param(
  [string]$Dir = ".",
  [string]$Filter = "*.docx"
)

$dir = (Resolve-Path -LiteralPath $Dir).Path
Get-ChildItem -LiteralPath $dir -Filter "~`$*" -Force -ErrorAction SilentlyContinue |
  Remove-Item -Force -ErrorAction SilentlyContinue

$item = Get-ChildItem -LiteralPath $dir -Filter $Filter |
  Where-Object { $_.Name -notlike '~$*' } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $item) { Write-Output "NO_DOCX"; exit 1 }

$Docx = $item.FullName
$Pdf = [System.IO.Path]::ChangeExtension($Docx, ".pdf")

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null
try {
  $doc = $word.Documents.Open($Docx, $false, $false)
  foreach ($story in $doc.StoryRanges) { $story.Fields.Update() | Out-Null }
  if ($doc.TablesOfContents.Count -gt 0) {
    for ($i = 1; $i -le $doc.TablesOfContents.Count; $i++) {
      $doc.TablesOfContents.Item($i).Update() | Out-Null
    }
  }
  foreach ($story in $doc.StoryRanges) { $story.Fields.Update() | Out-Null }
  $doc.Repaginate()
  Write-Output ("PAGES=" + $doc.ComputeStatistics(2))
  Write-Output ("WORDS=" + $doc.ComputeStatistics(0))
  $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 0, 0, 0, $true, $true, 0)
  Write-Output ("PDF=" + $Pdf)
} finally {
  # 0 = wdDoNotSaveChanges. Closing and quitting without it lets Word write the
  # file back and strip the explicit RTL markup, especially after an error.
  if ($doc) { $doc.Close(0) }
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}

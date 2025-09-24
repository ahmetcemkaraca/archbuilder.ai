param(
  [string]$RepoRoot = (Resolve-Path ".").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg){ Write-Host "[snapshot-context] $msg" -ForegroundColor Cyan }
function Write-Err([string]$msg){ Write-Host "[snapshot-context] $msg" -ForegroundColor Red }

$ctxDir = Join-Path $RepoRoot ".mds/context"
$ctxFile = Join-Path $ctxDir "current-context.md"
$histDir = Join-Path $ctxDir "history"

if(!(Test-Path $ctxFile)){
  Write-Err "current-context.md not found. Run scripts/rehydrate-context.ps1 first."
  exit 2
}

if(!(Test-Path $histDir)){
  New-Item -ItemType Directory -Path $histDir | Out-Null
}

# Determine next numeric id NNNN
$existing = Get-ChildItem -Path $histDir -Filter "*.md" | ForEach-Object { $_.BaseName } | Where-Object { $_ -match "^(\d{4})-context$" }
if($existing){
  $max = ($existing | ForEach-Object { [int]($_ -replace "-context","") } | Measure-Object -Maximum).Maximum
  $next = [int]$max + 1
} else {
  $next = 1
}
$name = "{0:0000}-context.md" -f $next
$target = Join-Path $histDir $name

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$header = "# Context Snapshot`n`n- Timestamp: $stamp`n"
$body = Get-Content -Raw -Path $ctxFile
Set-Content -Path $target -Value ($header + "`n" + $body) -Encoding UTF8

Write-Info ("Wrote snapshot: {0}" -f $target)
exit 0



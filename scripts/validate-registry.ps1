Param(
  [string]$RepoRoot = (Resolve-Path "..").Path
)

Write-Host "[validate-registry] Starting validation..."

$ident = Join-Path $RepoRoot "docs/registry/identifiers.json"
$endp  = Join-Path $RepoRoot "docs/registry/endpoints.json"
$schem = Join-Path $RepoRoot "docs/registry/schemas.json"

if (!(Test-Path $ident) -or !(Test-Path $endp) -or !(Test-Path $schem)) {
  Write-Error "Registry files are missing. Expected docs/registry/(identifiers|endpoints|schemas).json"
  exit 2
}

try {
  $null = Get-Content $ident | ConvertFrom-Json
  $null = Get-Content $endp  | ConvertFrom-Json
  $null = Get-Content $schem | ConvertFrom-Json
} catch {
  Write-Error "Registry files contain invalid JSON: $_"
  exit 3
}

# Lightweight heuristic: if there were code changes touching typical API dirs, ensure endpoints.json not empty
$gitRoot = $RepoRoot
Set-Location $gitRoot
$changed = git status --porcelain | Select-String -Pattern "(api|server|backend|routes|controller|service|src)"
if ($changed) {
  $endpoints = (Get-Content $endp | ConvertFrom-Json).endpoints
  if ($endpoints.Count -eq 0) {
    Write-Warning "Potential API changes detected but endpoints.json is empty."
    exit 4
  }
}

Write-Host "[validate-registry] OK"
exit 0


Param(
  [string]$RepoRoot = (Resolve-Path ".").Path
)

$ctxFile = Join-Path $RepoRoot ".mds/context/current-context.md"
$ident = Join-Path $RepoRoot "docs/registry/identifiers.json"
$endp  = Join-Path $RepoRoot "docs/registry/endpoints.json"
$schem = Join-Path $RepoRoot "docs/registry/schemas.json"

if (!(Test-Path $ident) -or !(Test-Path $endp) -or !(Test-Path $schem)) {
  Write-Error "Missing registry files; cannot rehydrate context."
  exit 2
}

$date = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$identJson = Get-Content $ident -Raw
$endpJson  = Get-Content $endp -Raw
$schemJson = Get-Content $schem -Raw

$content = @()
$content += "# Current Context"
$content += ""
$content += ("Tarih: {0}" -f $date)
$content += ""
$content += "## Registry Snapshots"
$content += "### identifiers.json"
$content += '```json'
$content += $identJson
$content += '```'
$content += ""
$content += "### endpoints.json"
$content += '```json'
$content += $endpJson
$content += '```'
$content += ""
$content += "### schemas.json"
$content += '```json'
$content += $schemJson
$content += '```'

$joined = [string]::Join([Environment]::NewLine, $content)
Set-Content -Path $ctxFile -Value $joined -Encoding UTF8
Write-Host "[rehydrate-context] Wrote $ctxFile"
exit 0


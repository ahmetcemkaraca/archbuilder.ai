param(
    [string]$SourceDir = ".github/instructions",
    [string]$OutDir = ".cursor/rules"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$m){ Write-Host "[generate] $m" -ForegroundColor Cyan }
function Sanitize-Name([string]$name){
    return ($name -replace "[^a-zA-Z0-9\-_.]", "-")
}

if(-not (Test-Path $SourceDir)){ throw "Source not found: $SourceDir" }
if(-not (Test-Path $OutDir)){ New-Item -ItemType Directory -Path $OutDir | Out-Null }

$files = Get-ChildItem -Path $SourceDir -Filter *.instructions.md -File | Sort-Object Name
foreach($f in $files){
    $raw = Get-Content -Raw -Path $f.FullName
    $applyMatch = [regex]::Match($raw, '(?m)^applyTo:\s*"([^"]+)"')
    $descMatch = [regex]::Match($raw, '(?m)^description:\s*(.+)$')
    $apply = if($applyMatch.Success){ $applyMatch.Groups[1].Value } else { '**/*' }
    $desc  = if($descMatch.Success){ $descMatch.Groups[1].Value.Trim() } else { "Instruction: $($f.Name)" }

    $globs = @()
    foreach($p in ($apply -split ',')){
        $p2 = $p.Trim()
        if(-not [string]::IsNullOrWhiteSpace($p2)){ $globs += $p2 }
    }
    if($globs.Count -eq 0){ $globs = @('**/*') }
    $globsYaml = '"' + ($globs -join '", "') + '"'

    # strip YAML header from source content
    $body = [regex]::Replace($raw, '(?s)^---.*?---\s*', '')

    $nameBase = [System.IO.Path]::GetFileNameWithoutExtension($f.Name) # e.g., ai-integration.instructions
    $nameBase = ($nameBase -replace '\.instructions$', '')
    $ruleName = Sanitize-Name("instructions-$nameBase")
    $outPath = Join-Path $OutDir ("$ruleName.mdc")

    $header  = "name: $ruleName`n"
    $header += "globs: [$globsYaml]`n"
    $header += "description: $desc`n---`n"
    $prefix  = "# Attached Instruction Copy`n(Source: $($f.FullName.Replace($pwd.Path + '\\','')))`n`n"
    $content = $header + $prefix + $body

    Set-Content -Path $outPath -Value $content -Encoding UTF8
    Write-Info "Generated: $outPath"
}

Write-Info "Done."


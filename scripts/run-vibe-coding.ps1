param(
    [string]$PromptFile = ".mds/todoprompt.md",
    [int]$StartFrom = 1,
    [switch]$NoGit,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn([string]$msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Get-PromptBlocks([string]$path){
    if(-not (Test-Path $path)){ throw "Prompt file not found: $path" }
    $raw = Get-Content -Raw -Path $path
    $parts = [regex]::Split($raw, "(?m)^(?=\d+\)\s+Prompt\s+)") | Where-Object { $_.Trim() -ne '' }
    $blocks = @()
    foreach($p in $parts){
        $lines = $p -split "`r?`n"
        $title = $lines[0]
        if($title -match "^(\d+)\)\s+Prompt\s+(\d+)\s+(.+)$"){
            $idx = [int]$matches[2]
        } else {
            # Fallback: use running count
            $idx = ($blocks.Count + 1)
        }
        $content = ($lines | Select-Object -Skip 1) -join "`r`n"
        $blocks += [pscustomobject]@{ Index=$idx; Title=$title; Content=$content }
    }
    return ($blocks | Sort-Object Index)
}

function Save-State([int]$currentIndex){
    $statePath = ".mds/context/vibe-state.json"
    $state = @{ currentIndex = $currentIndex; updatedAt = (Get-Date).ToString("s") }
    $json = $state | ConvertTo-Json -Depth 3
    $dir = Split-Path -Parent $statePath
    if(-not (Test-Path $dir)){ New-Item -ItemType Directory -Path $dir | Out-Null }
    Set-Content -Path $statePath -Value $json -Encoding UTF8
}

function Append-Log([string]$message){
    $logPath = ".mds/context/vibe-log.txt"
    $dir = Split-Path -Parent $logPath
    if(-not (Test-Path $dir)){ New-Item -ItemType Directory -Path $dir | Out-Null }
    Add-Content -Path $logPath -Value ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $message)
}

function Update-VersionNote([int]$upto){
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $note = "## auto — vibe cycle up to prompt $upto ($stamp)" + "`n" + "- Ran prompts up to $upto; updated context/logs" + "`n"
    Add-Content -Path "version.md" -Value $note
}

function Git-CommitIfEnabled([string]$msg){
    if($NoGit){ return }
    if($DryRun){ Write-Info "[DRY] git add/commit skipped"; return }
    try{
        git add -A | Out-Null
        git commit -m $msg | Out-Null
    } catch { Write-Warn "Git commit failed or nothing to commit: $($_.Exception.Message)" }
}

function Ensure-Paths(){
    foreach($p in @('.mds/context/history')){ if(-not (Test-Path $p)){ New-Item -ItemType Directory -Path $p | Out-Null } }
}

Ensure-Paths
$blocks = Get-PromptBlocks -path $PromptFile
if($blocks.Count -eq 0){ throw "No prompts found in $PromptFile" }

$startIdx = [Math]::Max(1, $StartFrom)
Write-Info "Total prompts: $($blocks.Count). Starting from: $startIdx"

$processed = 0
for($i = 0; $i -lt $blocks.Count; $i++){
    $b = $blocks[$i]
    if($b.Index -lt $startIdx){ continue }

    $titleLine = $b.Title
    $promptText = ($titleLine + "`r`n`r`n" + $b.Content)

    $currentPromptPath = ".mds/context/current-prompt.txt"
    Set-Content -Path $currentPromptPath -Value $promptText -Encoding UTF8

    try { Set-Clipboard -Value $promptText } catch { Write-Warn "Set-Clipboard failed; manually copy from $currentPromptPath" }

    Write-Host "" -ForegroundColor Gray
    Write-Info "Prompt $($b.Index) prepared and copied to clipboard. Paste into the agent, let it run, then press ENTER to continue..."
    if(-not $DryRun){ [void][System.Console]::ReadLine() }

    Append-Log ("Executed Prompt {0}: {1}" -f $b.Index, $titleLine)
    $histFile = ".mds/context/history/{0:0000}-prompt-{1:00}.md" -f $b.Index, $b.Index
    $histBody = "# Prompt $($b.Index)`r`n`r`n$titleLine`r`n`r`n- Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`r`n- Notes: (add outcome/links here)" 
    Set-Content -Path $histFile -Value $histBody -Encoding UTF8

    Save-State -currentIndex $b.Index
    $processed++

    if(($b.Index % 2) -eq 0){
        Update-VersionNote -upto $b.Index
        Git-CommitIfEnabled -msg ("chore(vibe): cycle up to prompt {0}" -f $b.Index)
    }
}

Write-Info "Completed. Processed: $processed prompts."


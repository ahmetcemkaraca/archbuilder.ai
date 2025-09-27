# ArchBuilder.AI Development Scripts for Windows
# Usage: .\dev-tools.ps1 -Action format

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("format", "lint", "test", "install-dev", "setup", "clean", "dev-setup", "help")]
    [string]$Action
)

function Show-Help {
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  .\dev-tools.ps1 -Action format     - Format all Python code with black and isort" -ForegroundColor Yellow
    Write-Host "  .\dev-tools.ps1 -Action lint       - Run linting with flake8" -ForegroundColor Yellow
    Write-Host "  .\dev-tools.ps1 -Action test       - Run tests with pytest" -ForegroundColor Yellow
    Write-Host "  .\dev-tools.ps1 -Action install-dev - Install development dependencies" -ForegroundColor Yellow
    Write-Host "  .\dev-tools.ps1 -Action setup      - Setup pre-commit hooks" -ForegroundColor Yellow
    Write-Host "  .\dev-tools.ps1 -Action clean      - Clean cache and temp files" -ForegroundColor Yellow
    Write-Host "  .\dev-tools.ps1 -Action dev-setup  - Complete development setup" -ForegroundColor Yellow
}

function Format-Code {
    Write-Host "🔧 Formatting Python code..." -ForegroundColor Blue
    python -m black src\cloud-server\app --line-length=88
    python -m isort src\cloud-server\app --profile=black --line-length=88
    Write-Host "✅ Code formatting complete!" -ForegroundColor Green
}

function Lint-Code {
    Write-Host "🔍 Running linting checks..." -ForegroundColor Blue
    python -m flake8 src\cloud-server\app --count --select=E9,F63,F7,F82 --show-source --statistics
    python -m black --check --diff src\cloud-server\app
    python -m isort --check-only --diff src\cloud-server\app --profile=black
    Write-Host "✅ Linting complete!" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Blue
    Set-Location src\cloud-server
    python -m pytest tests\ -v
    Set-Location ..\..
    Write-Host "✅ Tests complete!" -ForegroundColor Green
}

function Install-DevDependencies {
    Write-Host "📦 Installing development dependencies..." -ForegroundColor Blue
    python -m pip install --upgrade pip
    pip install -r src\cloud-server\requirements.txt
    pip install -r src\cloud-server\requirements-dev.txt
    Write-Host "✅ Development dependencies installed!" -ForegroundColor Green
}

function Setup-PreCommit {
    Write-Host "🔗 Setting up pre-commit hooks..." -ForegroundColor Blue
    pip install pre-commit
    pre-commit install
    Write-Host "✅ Pre-commit hooks installed!" -ForegroundColor Green
}

function Clean-Cache {
    Write-Host "🧹 Cleaning cache and temporary files..." -ForegroundColor Blue
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Name "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Name "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Name "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
}

function Dev-Setup {
    Install-DevDependencies
    Setup-PreCommit
    Write-Host "🚀 Development environment ready!" -ForegroundColor Green
}

# Execute action
switch ($Action) {
    "format" { Format-Code }
    "lint" { Lint-Code }
    "test" { Run-Tests }
    "install-dev" { Install-DevDependencies }
    "setup" { Setup-PreCommit }
    "clean" { Clean-Cache }
    "dev-setup" { Dev-Setup }
    "help" { Show-Help }
}

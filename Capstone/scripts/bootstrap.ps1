Param(
    [switch]$SkipToolChecks
)

$ErrorActionPreference = "Stop"

Write-Host "[Phase0] Creating virtual environment" -ForegroundColor Cyan
python -m venv .venv

$venvPython = Join-Path ".venv" "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements-dev.txt

if (-not $SkipToolChecks) {
    Write-Host "[Phase0] Verifying pinned tool versions" -ForegroundColor Cyan
    $versions = Get-Content "config/tool-versions.json" | ConvertFrom-Json

    $pythonVersion = (& $venvPython --version) -replace "Python ", ""
    if ($pythonVersion -notlike "$($versions.python)*") {
        throw "Python version mismatch. Expected $($versions.python), got $pythonVersion"
    }

    $azVersion = az version --query '"azure-cli"' -o tsv
    if ($azVersion -ne $versions.az) {
        throw "Azure CLI version mismatch. Expected $($versions.az), got $azVersion"
    }

    $bicepVersion = (az bicep version) -replace "Bicep CLI version ", ""
    if ($bicepVersion -ne $versions.bicep) {
        throw "Bicep version mismatch. Expected $($versions.bicep), got $bicepVersion"
    }

    $cfnLintVersion = (& $venvPython -m cfnlint --version)
    if ($cfnLintVersion -notlike "*$($versions.'cfn-lint')*") {
        throw "cfn-lint version mismatch. Expected $($versions.'cfn-lint'), got $cfnLintVersion"
    }

    $checkovVersion = (& $venvPython -m checkov --version)
    if ($checkovVersion -notlike "*$($versions.checkov)*") {
        throw "checkov version mismatch. Expected $($versions.checkov), got $checkovVersion"
    }
}

Write-Host "[Phase0] Bootstrap completed successfully" -ForegroundColor Green

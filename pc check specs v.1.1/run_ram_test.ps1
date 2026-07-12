<#
Robust PowerShell runner that invokes `ram_test.py` from the script directory.
Usage: Right-click and Run with PowerShell, or run in PowerShell:
.\run_ram_test.ps1
#>
Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir
try {
    $py = "python"
    $script = Join-Path $scriptDir 'ram_test.py'
    if (-not (Test-Path $script)) {
        Write-Error "Script not found: $script"
        exit 1
    }
    # Call python with full script path to avoid cwd issues
    & $py $script --json-path (Join-Path $scriptDir 'launch.json.txt')
    $exit = $LASTEXITCODE
    exit $exit
} finally {
    Pop-Location
}

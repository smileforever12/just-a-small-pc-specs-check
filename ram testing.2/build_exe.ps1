<# Build an EXE using PyInstaller. Run in an elevated PowerShell if needed. #>
Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    pyinstaller --onefile --name ram_test ram_test.py
    Write-Host "If successful, the EXE will be in the 'dist' folder: $scriptDir\dist\ram_test.exe"
} finally {
    Pop-Location
}

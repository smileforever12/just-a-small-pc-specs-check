<# Build an EXE using PyInstaller. Run in an elevated PowerShell if needed. #>
Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    $icon = Join-Path $scriptDir 'app_icon.ico'
    $args = @('--onefile','--name','ram_test','ram_test.py')
    if (Test-Path $icon) {
        Write-Host "Using icon: $icon"
        $args = @('--onefile','--name','ram_test','--icon', $icon, 'ram_test.py')
    } else {
        Write-Host "No app_icon.ico found. Building without custom icon. To include an icon, place 'app_icon.ico' in this folder before running this script."
    }
    & pyinstaller @args
    if (Test-Path (Join-Path $scriptDir 'dist\ram_test.exe')) {
        Write-Host "Build successful: $scriptDir\dist\ram_test.exe"
    } else {
        Write-Error "Build finished but EXE not found in dist. Check PyInstaller output for errors."
    }
} finally {
    Pop-Location
}

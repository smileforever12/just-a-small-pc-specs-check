@echo off
REM Build EXE using PyInstaller (Windows cmd)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if exist "%~dp0app_icon.ico" (
	pyinstaller --onefile --name ram_test --icon "%~dp0app_icon.ico" ram_test.py
) else (
	pyinstaller --onefile --name ram_test ram_test.py
)
if exist "%~dp0dist\ram_test.exe" (
	echo Build successful: dist\ram_test.exe
) else (
	echo Build finished but dist\ram_test.exe not found. Check PyInstaller output.
)

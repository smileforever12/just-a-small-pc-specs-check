@echo off
REM Launcher for ram_test.py that runs from the script directory and keeps window open.
cd /d %~dp0
cd /d %~dp0
if exist "%~dp0dist\ram_test.exe" (
	"%~dp0dist\ram_test.exe"
) else if exist "%~dp0ram_test.exe" (
	"%~dp0ram_test.exe"
) else (
	python ram_test.py --json-path launch.json.txt --pause-on-exit
)
pause

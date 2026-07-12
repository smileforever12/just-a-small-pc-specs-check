@echo off
REM Launcher for ram_test.py that runs from the script directory and keeps window open.
cd /d %~dp0
python ram_test.py --json-path launch.json.txt --pause-on-exit
pause

@echo off
REM Build EXE using PyInstaller (Windows cmd)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pyinstaller --onefile --name ram_test ram_test.py
echo If successful, EXE is in dist\ram_test.exe

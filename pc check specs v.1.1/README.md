i recommmend downloading python first then run it 


# RAM test launcher (Python)

This repository contains a small Python script that reads a JSON configuration file and runs a simple RAM test by allocating memory or monitoring available memory.

Usage:

1. Edit or place your JSON config in `launch.json.txt` in the same folder. Example keys:

- `durationSeconds`: total run time in seconds (default: 30)
- `targetMB`: target amount of memory to allocate in MB (default: 1024)
- `chunkMB`: allocation chunk size in MB (default: 50)
- `waitBetweenChunksMs`: milliseconds to wait between chunk allocations (default: 100)
- `mode`: `allocate` (allocate memory) or `monitor` (report available memory) (default: `allocate`)

2. Run the script with Python 3:

```powershell
python ram_test.py --json-path launch.json.txt
```

Notes:

- This script deliberately allocates memory for testing; run carefully on machines where memory pressure is acceptable.
- The script releases memory at the end and triggers garbage collection.
- The monitor mode reports system available memory; process RSS is reported when `psutil` is installed.

Additional utility:

- `ram_info.py`: reports installed RAM total and per-module speeds (Windows via `wmic`, Linux via `dmidecode` when available).
Additionally, `ram_test.py` now reports CPU and GPU information at startup.

GPU detection uses `GPUtil` if available, otherwise falls back to `nvidia-smi` or `wmic` on Windows.
Install extras with:

```powershell
python -m pip install psutil GPUtil
```

- `ram_info.py`: reports installed RAM total and per-module speeds (Windows via `wmic`, Linux via `dmidecode` when available).

Usage:

```powershell
python ram_info.py
```

Requirements:

- `psutil` (install with `pip install psutil`).

Troubleshooting: PowerShell "file not found"

- If PowerShell reports it can't find the file, make sure you either change directory into the project folder or use the included wrapper which resolves the paths automatically:

```powershell
Set-Location 'C:\Users\smile\ram testing.2'
.\run_ram_test.ps1
```

or from anywhere:

```powershell
python 'C:\Users\smile\ram testing.2\ram_test.py' --json-path 'C:\Users\smile\ram testing.2\launch.json.txt'
```

Create a Windows EXE

- To build a single-file EXE from `ram_test.py` using PyInstaller, run one of the included build scripts. They will install requirements and produce `dist\ram_test.exe`:

- To include a custom icon in the EXE, place your ICO file named `app_icon.ico` in the project root before running the build script. The build scripts will detect and include it automatically.

- To build a single-file EXE from `ram_test.py` using PyInstaller, run one of the included build scripts. They will install requirements and produce `dist\ram_test.exe`:

PowerShell:
```powershell
Set-Location 'C:\Users\smile\ram testing.2'
.\build_exe.ps1
```

CMD:
```bat
cd /d C:\Users\smile\ram testing.2
build_exe.bat
```

Notes:

- Building an EXE can take a minute. `pyinstaller` bundles a Python interpreter and dependencies into the EXE.
- If you want the EXE to include `psutil`, it is listed in `requirements.txt` and will be bundled.



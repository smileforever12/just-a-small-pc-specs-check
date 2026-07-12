#!/usr/bin/env python3
import argparse
import json
import time
import os
import gc
import sys
import platform
import subprocess
import shutil
import csv

# Optional dependency: psutil. If missing, the script will still run with reduced info.
try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    psutil = None
    HAS_PSUTIL = False

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_available_mb():
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullAvailPhys / (1024 * 1024)
    except Exception:
        return None

def get_process_private_mb():
    try:
        if not HAS_PSUTIL:
            return None
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)
    except Exception:
        return None

def monitor_loop(duration, wait_ms):
    end = time.time() + duration
    while time.time() < end:
        avail = get_available_mb()
        proc = get_process_private_mb()
        ts = time.strftime('%Y-%m-%dT%H:%M:%S')
        parts = [f"{ts}"]
        if avail is not None:
            parts.append(f"AvailableMB: {avail:.2f}")
        if proc is not None:
            parts.append(f"ProcessRSSMB: {proc:.2f}")
        print(' '.join(parts))
        time.sleep(wait_ms / 1000.0)

def allocate_loop(target_mb, chunk_mb, duration, wait_ms):
    allocated = []
    allocated_mb = 0
    end = time.time() + duration
    try:
        while allocated_mb < target_mb and time.time() < end:
            size = chunk_mb * 1024 * 1024
            # allocate a bytes object and keep a reference
            b = bytearray(os.urandom(size))
            allocated.append(b)
            allocated_mb += chunk_mb
            print(f"Allocated {allocated_mb} MB")
            time.sleep(wait_ms / 1000.0)
        print("Holding allocation until duration ends...")
        while time.time() < end:
            time.sleep(1)
    except MemoryError:
        print("MemoryError during allocation; releasing what we have.")
    finally:
        allocated = None
        gc.collect()
        print("Released memory; exiting.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json-path', default='launch.json.txt')
    ap.add_argument('--pause-on-exit', action='store_true', help='Pause and wait for Enter before exiting (useful when double-clicking)')
    args = ap.parse_args()

    if not os.path.exists(args.json_path):
        print(f"Config file not found: {args.json_path} — using internal defaults.")
        cfg = {
            'durationSeconds': 30,
            'targetMB': 1024,
            'chunkMB': 50,
            'waitBetweenChunksMs': 100,
            'mode': 'allocate'
        }
    else:
        cfg = load_config(args.json_path)
    duration = int(cfg.get('durationSeconds', 30))
    target_mb = int(cfg.get('targetMB', 1024))
    chunk_mb = int(cfg.get('chunkMB', 50))
    wait_ms = int(cfg.get('waitBetweenChunksMs', 100))
    mode = cfg.get('mode', 'allocate').lower()

    # Report CPU and GPU info
    def get_cpu_info():
        info = {}
        # Logical/physical core counts and frequency via psutil when available
        if HAS_PSUTIL:
            info['logical_cpus'] = psutil.cpu_count(logical=True)
            info['physical_cpus'] = psutil.cpu_count(logical=False)
            try:
                freq = psutil.cpu_freq()
                if freq:
                    info['max_mhz'] = int(freq.max or freq.current)
            except Exception:
                pass
        else:
            info['logical_cpus'] = os.cpu_count()
            info['physical_cpus'] = None
        # Try platform-specific name
        name = None
        try:
            if platform.system() == 'Windows':
                out = subprocess.check_output(['wmic', 'cpu', 'get', 'Name,MaxClockSpeed', '/format:csv'], stderr=subprocess.DEVNULL)
                lines = out.decode(errors='ignore').splitlines()
                reader = csv.DictReader([l for l in lines if l.strip()])
                for row in reader:
                    name = row.get('Name')
                    if 'MaxClockSpeed' in row and row.get('MaxClockSpeed'):
                        info['max_mhz'] = int(row.get('MaxClockSpeed'))
                    break
            elif platform.system() == 'Linux':
                if os.path.exists('/proc/cpuinfo'):
                    with open('/proc/cpuinfo', 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if 'model name' in line.lower():
                                name = line.split(':',1)[1].strip()
                                break
            if not name:
                name = platform.processor() or platform.uname().processor or platform.uname().machine
        except Exception:
            name = name or platform.processor()
        # If physical core count missing or zero, try WMIC on Windows
        if platform.system() == 'Windows' and (not info.get('physical_cpus') or info.get('physical_cpus') == 0):
            try:
                out = subprocess.check_output(['wmic', 'cpu', 'get', 'NumberOfCores,NumberOfLogicalProcessors', '/format:csv'], stderr=subprocess.DEVNULL)
                lines = out.decode(errors='ignore').splitlines()
                reader = csv.DictReader([l for l in lines if l.strip()])
                cores = 0
                log = 0
                for row in reader:
                    try:
                        cores += int(row.get('NumberOfCores') or 0)
                    except Exception:
                        pass
                    try:
                        log += int(row.get('NumberOfLogicalProcessors') or 0)
                    except Exception:
                        pass
                if cores > 0:
                    info['physical_cpus'] = cores
                if log > 0 and not info.get('logical_cpus'):
                    info['logical_cpus'] = log
            except Exception:
                pass
        info['name'] = name
        return info

    def get_gpu_info():
        gpus = []
        # Try GPUtil
        try:
            import GPUtil
            for g in GPUtil.getGPUs():
                gpus.append({'name': g.name, 'memoryTotalMB': int(g.memoryTotal)})
            if gpus:
                return gpus
        except Exception:
            pass
        # Try nvidia-smi
        try:
            if shutil.which('nvidia-smi'):
                out = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], stderr=subprocess.DEVNULL)
                for line in out.decode(errors='ignore').splitlines():
                    parts = [p.strip() for p in line.split(',')]
                    if parts:
                        name = parts[0]
                        mem = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                        gpus.append({'name': name, 'memoryTotalMB': mem})
                if gpus:
                    return gpus
        except Exception:
            pass
        # Try wmic (Windows)
        try:
            if platform.system() == 'Windows':
                out = subprocess.check_output(['wmic', 'path', 'win32_VideoController', 'get', 'Name,AdapterRAM', '/format:csv'], stderr=subprocess.DEVNULL)
                lines = out.decode(errors='ignore').splitlines()
                reader = csv.DictReader([l for l in lines if l.strip()])
                for row in reader:
                    name = row.get('Name')
                    ram = 0
                    try:
                        ram = int(row.get('AdapterRAM') or 0) // (1024*1024)
                    except Exception:
                        ram = 0
                    gpus.append({'name': name, 'memoryTotalMB': ram})
                if gpus:
                    return gpus
        except Exception:
            pass
        return None

    cpu = get_cpu_info()
    gpus = get_gpu_info()
    print('CPU:')
    print(f" Name: {cpu.get('name', 'N/A')}")
    print(f" Physical cores: {cpu.get('physical_cpus', 'N/A')}, Logical: {cpu.get('logical_cpus', 'N/A')}")
    if cpu.get('max_mhz'):
        print(f" Max clock: {cpu.get('max_mhz')} MHz")
    if not HAS_PSUTIL:
        print('Note: `psutil` not installed — install with `pip install psutil` for more details.')
    if gpus:
        print('GPU(s):')
        for i,g in enumerate(gpus,1):
            print(f" {i}. {g.get('name','N/A')} - {g.get('memoryTotalMB',0)} MB")
    else:
        print('GPU: No GPU information available')

    print(f"Mode: {mode}; TargetMB: {target_mb}; Duration: {duration}s; ChunkMB: {chunk_mb}")

    try:
        if mode == 'monitor':
            monitor_loop(duration, wait_ms)
        else:
            allocate_loop(target_mb, chunk_mb, duration, wait_ms)
    except Exception as e:
        print('Error during run:', e)
        raise
    finally:
        if getattr(args, 'pause_on_exit', False):
            try:
                input('Press Enter to exit...')
            except Exception:
                pass

if __name__ == '__main__':
    main()

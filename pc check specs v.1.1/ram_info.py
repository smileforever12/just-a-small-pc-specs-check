#!/usr/bin/env python3
"""Report installed RAM total and module speeds (Windows via WMI/WMIC, Linux via dmidecode if available).

Usage: python ram_info.py
"""
import platform
import subprocess
import sys
try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    psutil = None
    HAS_PSUTIL = False
import csv


def bytes_to_mb(b):
    return b / (1024 * 1024)


def report_windows():
    try:
        out = subprocess.check_output([
            'wmic', 'memorychip', 'get', 'Capacity,Speed,Manufacturer,PartNumber,BankLabel', '/format:csv'
        ], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print('wmic not found on this system.')
        return None
    text = out.decode(errors='ignore').strip().splitlines()
    if len(text) < 2:
        print('No memory module data returned by wmic.')
        return None
    reader = csv.DictReader(text)
    modules = []
    for row in reader:
        try:
            cap = int(row.get('Capacity') or 0)
        except ValueError:
            cap = 0
        try:
            speed = int(row.get('Speed') or 0)
        except ValueError:
            speed = 0
        modules.append({
            'bank': row.get('BankLabel') or '',
            'capacity': cap,
            'speed': speed,
            'manufacturer': row.get('Manufacturer') or '',
            'part': row.get('PartNumber') or ''
        })
    return modules


def report_linux():
    # Try dmidecode if available
    try:
        out = subprocess.check_output(['dmidecode', '--type', '17'], stderr=subprocess.DEVNULL)
        text = out.decode(errors='ignore')
    except Exception:
        return None
    modules = []
    cur = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if cur:
                modules.append(cur)
                cur = {}
            continue
        if line.startswith('Size:'):
            val = line.split(':',1)[1].strip()
            if val.lower().endswith('mb'):
                try:
                    cur['capacity'] = int(val[:-2].strip()) * 1024 * 1024
                except Exception:
                    cur['capacity'] = 0
            elif val.lower().endswith('gb'):
                try:
                    cur['capacity'] = int(val[:-2].strip()) * 1024 * 1024 * 1024
                except Exception:
                    cur['capacity'] = 0
            else:
                cur['capacity'] = 0
        elif line.startswith('Speed:'):
            try:
                cur['speed'] = int(line.split(':',1)[1].strip().split()[0])
            except Exception:
                cur['speed'] = 0
        elif line.startswith('Manufacturer:'):
            cur['manufacturer'] = line.split(':',1)[1].strip()
        elif line.startswith('Part Number:'):
            cur['part'] = line.split(':',1)[1].strip()
    if cur:
        modules.append(cur)
    return modules


def print_report(modules):
    if not modules:
        print('No per-module data available on this platform or requires elevated privileges.')
        return
    total = sum(m.get('capacity',0) for m in modules)
    speeds = [m.get('speed',0) for m in modules if m.get('speed',0)]
    print('Modules:')
    for i,m in enumerate(modules,1):
        cap_mb = bytes_to_mb(m.get('capacity',0))
        speed = m.get('speed',0)
        print(f" {i}. Bank={m.get('bank','') or m.get('part','') or 'N/A'} Capacity={cap_mb:.0f} MB Speed={speed} MHz Manufacturer={m.get('manufacturer','')}")
    print(f"Total (modules): {bytes_to_mb(total):.0f} MB")
    if speeds:
        print(f"Speed (min/avg/max): {min(speeds)} / {sum(speeds)//len(speeds)} / {max(speeds)} MHz")


def main():
    print('Gathering system RAM info...')
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        print(f"Total system memory (psutil): {bytes_to_mb(vm.total):.0f} MB")
    else:
        # Fallbacks for total memory
        total = None
        try:
            if platform.system() == 'Windows':
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
                total = stat.ullTotalPhys
            elif platform.system() == 'Linux':
                with open('/proc/meminfo', 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            parts = line.split()
                            # value is in kB
                            total = int(parts[1]) * 1024
                            break
        except Exception:
            total = None
        if total:
            print(f"Total system memory (fallback): {bytes_to_mb(total):.0f} MB")
        else:
            print('Total system memory: unknown (install psutil for better info)')

    system = platform.system()
    modules = None
    if system == 'Windows':
        modules = report_windows()
    elif system == 'Linux':
        modules = report_linux()
    else:
        print(f'Platform {system} has no module-level helper implemented.')

    print_report(modules)


if __name__ == '__main__':
    main()

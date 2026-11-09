"""Read a host's live load: CPU counters, memory, disk, temperature and per-service cgroup usage.

Sent over SSH like agent.py. Only reads /proc and /sys; it starts no other program.
The caller turns two counter readings into percentages.
"""
import json
import os
from pathlib import Path
import time


def read(path, default=''):
    try:
        return Path(path).read_text()
    except OSError:
        return default


def cpu():
    # Aggregate jiffies: busy and total since boot.
    fields = [int(v) for v in read('/proc/stat').splitlines()[0].split()[1:]]
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return sum(fields[:8]) - idle, sum(fields[:8])


def memory():
    info = {}
    for line in read('/proc/meminfo').splitlines():
        key, _, rest = line.partition(':')
        info[key] = int(rest.split()[0]) * 1024 if rest.split() else 0
    return info.get('MemTotal', 0), info.get('MemTotal', 0) - info.get('MemAvailable', 0)


def temperature():
    # Prefer the CPU package sensor; fall back to the hottest thermal zone.
    best, package = None, None
    for zone in Path('/sys/class/thermal').glob('thermal_zone*'):
        try:
            value = int(read(zone / 'temp', '0')) / 1000
        except ValueError:
            continue
        if not 0 < value < 130:
            continue
        if read(zone / 'type').strip() in ('x86_pkg_temp', 'cpu-thermal', 'k10temp'):
            package = value
        best = max(best or 0, value)
    if package is None:
        for hwmon in Path('/sys/class/hwmon').glob('hwmon*'):
            if read(hwmon / 'name').strip() in ('coretemp', 'k10temp', 'zenpower'):
                try:
                    package = int(read(hwmon / 'temp1_input', '0')) / 1000
                except ValueError:
                    pass
    return round(package if package is not None else best, 1) if (package or best) else None


def battery():
    for bat in sorted(Path('/sys/class/power_supply').glob('BAT*')):
        try:
            return {'percent': int(read(bat / 'capacity')), 'status': read(bat / 'status').strip()}
        except ValueError:
            continue
    return None


def cgroups():
    # Services and containers by cgroup leaf: CPU time in microseconds and current memory in bytes.
    out = {}
    root = Path('/sys/fs/cgroup')
    for directory, subdirs, files in os.walk(root):
        name = os.path.basename(directory)
        # user@UID.service only holds the user's own units; descend into it instead of counting it.
        if name.startswith('user@'):
            continue
        if not (name.endswith('.service') or (name.startswith('docker-') and name.endswith('.scope'))):
            continue
        subdirs[:] = []
        usage = 0
        for line in read(os.path.join(directory, 'cpu.stat')).splitlines():
            if line.startswith('usage_usec '):
                usage = int(line.split()[1])
        try:
            mem = int(read(os.path.join(directory, 'memory.current'), '0') or 0)
        except ValueError:
            mem = 0
        scope = 'user' if '/user@' in directory else 'system'
        key = name if name.startswith('docker-') else scope + ':' + name
        if key not in out or usage > out[key][0]:
            out[key] = [usage, mem]
    return out


def main():
    total, used = memory()
    disk = os.statvfs('/')
    busy, all_ = cpu()
    release = dict(line.split('=', 1) for line in read('/etc/os-release').splitlines() if '=' in line)
    model = next((l.split(':', 1)[1].strip() for l in read('/proc/cpuinfo').splitlines() if l.startswith('model name')), '')
    print(json.dumps({
        'time': time.time(),
        'cpu': [busy, all_],
        'cores': os.cpu_count(),
        'cpu_model': model,
        'os': release.get('PRETTY_NAME', '').strip('"'),
        'load': [float(v) for v in read('/proc/loadavg').split()[:3]],
        'uptime': float(read('/proc/uptime', '0').split()[0]),
        'mem': [used, total],
        'disk': [(disk.f_blocks - disk.f_bfree) * disk.f_frsize, (disk.f_blocks - disk.f_bfree + disk.f_bavail) * disk.f_frsize],
        'temp': temperature(),
        'battery': battery(),
        'cgroups': cgroups(),
    }))


if __name__ == '__main__':
    main()

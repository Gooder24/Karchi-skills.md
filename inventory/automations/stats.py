"""Read a host's live load: CPU counters, memory, disk, temperature and per-service cgroup usage.

Sent over SSH like agent.py. Only reads /proc and /sys. Protected RAPL counters
are read with one non-interactive sudo cat; no permissions or settings change.
The caller turns two counter readings into percentages.
"""
import json
import os
from pathlib import Path
import subprocess
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


def cpu_topology(info):
    records = []
    for block in info.split('\n\n'):
        fields = {key.strip(): value.strip() for line in block.splitlines()
                  if ':' in line for key, value in [line.split(':', 1)]}
        if 'processor' in fields:
            records.append(fields)
    threads = len(records) or os.cpu_count()
    virtualized = bool(read('/sys/hypervisor/type').strip()) or any(
        'hypervisor' in r.get('flags', '').split() for r in records)
    cores = None
    if records and not virtualized:
        try:
            pairs = {(int(r['physical id']), int(r['core id'])) for r in records}
            if all(socket >= 0 and core >= 0 for socket, core in pairs):
                cores = len(pairs)
        except (KeyError, ValueError):
            pass
    return cores, threads, virtualized


def graphics():
    devices = []
    for device in sorted(Path('/sys/bus/pci/devices').glob('*')):
        if not read(device / 'class').strip().startswith('0x03'):
            continue
        try:
            devices.append({'address': device.name,
                            'vendor': f"{int(read(device / 'vendor'), 16):04x}",
                            'device': f"{int(read(device / 'device'), 16):04x}"})
        except ValueError:
            continue
    return devices


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


def battery_watts():
    # A battery on AC can report zero while the laptop still draws power from its adapter.
    supplies = Path('/sys/class/power_supply')
    if any(read(p / 'type').strip() in ('Mains', 'USB', 'USB_C', 'USB_PD') and
           read(p / 'online').strip() == '1' for p in supplies.glob('*')):
        return None
    total, discharging = 0, False
    for bat in supplies.glob('BAT*'):
        if read(bat / 'present').strip() == '0':
            continue
        status = read(bat / 'status').strip()
        if status in ('Not charging', 'Full'):
            continue
        if status != 'Discharging':
            return None
        discharging = True
        try:
            raw = read(bat / 'power_now').strip()
            watts = int(raw) / 1e6 if raw else int(read(bat / 'current_now')) * int(read(bat / 'voltage_now')) / 1e12
        except ValueError:
            return None
        if watts < 0:
            return None
        total += watts
    return round(total, 2) if discharging else None


def package_energy():
    # Package includes its child domains: summing cores/uncore or the MMIO mirror counts twice.
    packages, protected, expected = {}, [], set()
    for zone in sorted(Path('/sys/class/powercap').glob('intel-rapl:*')):
        if not read(zone / 'name').strip().startswith('package-'):
            continue
        expected.add(zone.name)
        try:
            maximum = int(read(zone / 'max_energy_range_uj'))
            try:
                energy = int((zone / 'energy_uj').read_text())
            except PermissionError:
                protected.append((zone, maximum))
                continue
            packages[zone.name] = [energy, maximum]
        except (OSError, ValueError):
            continue
    if protected:
        try:
            result = subprocess.run(['sudo', '-n', 'cat', '--', *[str(p / 'energy_uj') for p, _ in protected]],
                                    capture_output=True, text=True, timeout=2)
            values = result.stdout.splitlines()
            if result.returncode == 0 and len(values) == len(protected):
                packages.update({p.name: [int(value), maximum] for (p, maximum), value in zip(protected, values)})
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    # A partial multi-socket reading would understate total CPU power.
    return packages if packages.keys() == expected else {}


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
    info = read('/proc/cpuinfo')
    model = next((l.split(':', 1)[1].strip() for l in info.splitlines() if l.startswith('model name')), '')
    cores, threads, virtualized = cpu_topology(info)
    print(json.dumps({
        'time': time.time(),
        'cpu': [busy, all_],
        'cores': cores,
        'threads': threads,
        'virtualized': virtualized,
        'cpu_model': model,
        'gpus': graphics(),
        'os': release.get('PRETTY_NAME', '').strip('"'),
        'load': [float(v) for v in read('/proc/loadavg').split()[:3]],
        'uptime': float(read('/proc/uptime', '0').split()[0]),
        'boot_id': read('/proc/sys/kernel/random/boot_id').strip(),
        'mem': [used, total],
        'disk': [(disk.f_blocks - disk.f_bfree) * disk.f_frsize, (disk.f_blocks - disk.f_bfree + disk.f_bavail) * disk.f_frsize],
        'temp': temperature(),
        'battery': battery(),
        'power': {'packages': package_energy(), 'battery_w': battery_watts()},
        'cgroups': cgroups(),
    }))


if __name__ == '__main__':
    main()

"""Read a host's own schedulers without modifying them.

Transmitted over SSH, with a JSON request on stdin. No shell commands come from the client.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import sys

HOME = Path.home()
ERRORS = []
ROWS = []


def run(args, stdin=None, ok=(0,), timeout=12):
    p = subprocess.run(args, input=stdin, text=True, capture_output=True, timeout=timeout)
    if p.returncode not in ok:
        raise RuntimeError(f'{args[0]}: exit {p.returncode}')
    return p.stdout


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def redact(text):
    text = str(text or '')
    text = re.sub(r'(?i)(authorization\s*:\s*)(?:bearer|basic|token)\s+[^\s\'\"]+', r'\1[skryté]', text)
    text = re.sub(r'\b(?:sk-(?:ant-)?[\w-]+|gh[pousr]_[\w]+|github_pat_[\w]+)\b', '[skryté]', text)
    text = re.sub(r'(?i)/bot\d+:[\w-]+', '/bot[skryté]', text)
    text = re.sub(r'''\b([A-Z][A-Z0-9_]*\s*=\s*)("[^"]*"|'[^']*'|[^\s;&]+)''', r'\1[skryté]', text)
    text = re.sub(r'''(?i)((?:--[\w-]*(?:token|password|passwd|secret|key|credential|pass|auth)[\w-]*|-u|--user)\s+)("[^"]*"|'[^']*'|[^\s]+)''', r'\1[skryté]', text)
    text = re.sub(r'(?<!\w)-p[^\s]+', '-p[skryté]', text)
    text = re.sub(r'''(?i)(\b(?:key|pass|pat)\s*[=:]\s*)("[^"]*"|'[^']*'|[^\s;&]+)''', r'\1[skryté]', text)
    text = re.sub(r'''(?i)((?:[\w-]*(?:token|password|passwd|secret|api[_-]?key)[\w-]*)\s*[=:]\s*)("[^"]*"|'[^']*')''', r'\1[skryté]', text)
    text = re.sub(r'(?i)((?:[\w-]*(?:token|password|passwd|secret|api[_-]?key)[\w-]*)\s*[=:]\s*)[^\s;,]+', r'\1[skryté]', text)
    text = re.sub(r'''(?i)(--(?:token|password|secret|api-key)\s+)("[^"]*"|'[^']*'|[^\s]+)''', r'\1[skryté]', text)
    text = re.sub(r'(?i)(bearer\s+)[\w.\-]+', r'\1[skryté]', text)
    text = re.sub(r'(https?://)[^\s/@]+:[^\s/@]+@', r'\1[skryté]@', text)
    return text[:2000]


def display_command(raw):
    """Expose the executable/script, never arbitrary arguments or inline shell code."""
    match = re.search(r'argv\[\]=([^;]+)', raw)
    text = match[1].strip() if match else raw
    try:
        words = shlex.split(text)
        while words and re.match(r'^[A-Za-z_][\w]*=', words[0]):
            words.pop(0)
        if not words:
            return ''
        program = words[0]
        shown = [program]
        if re.fullmatch(r'(?:python[\d.]*|bash|sh|node|ruby|perl)', Path(program).name):
            for word in words[1:]:
                if word.startswith('-'):
                    if Path(program).name.startswith('python') and word in ('-I', '-B', '-E', '-s', '-S', '-u', '-q'):
                        continue
                    # Unknown options may consume a secret value or contain inline shell code.
                    break
                if re.fullmatch(r'[\w/$~.{}-]+', word):
                    shown.append(word)
                break
        suffix = ' [ostatné argumenty skryté]' if len(words) > len(shown) else ''
        return redact(' '.join(shown)) + suffix
    except ValueError:
        return '[program sa nepodarilo bezpečne prečítať]'


def add(kind, key, name, definition, **data):
    ROWS.append(dict(kind=kind, key=key, name=redact(name), revision=digest(definition), **data))


def source(name, fn):
    try:
        fn()
    except Exception as e:
        ERRORS.append(dict(source=name, error=type(e).__name__ + ': ' + str(e)[:120]))


def ctl(scope, *args):
    return run(['systemctl', *( ['--user'] if scope == 'user' else []), *args])


PROPERTIES = '--property=Id,Description,FragmentPath,ActiveState,UnitFileState,Result,ExecMainStatus,ExecMainExitTimestamp,ExecMainStartTimestamp,NextElapseUSecRealtime,NextElapseUSecMonotonic,TimersCalendar,TimersMonotonic,ExecStart,Unit,TriggeredBy'


def parse_properties(text):
    values = {}
    for line in text.splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key] = values[key] + '\n' + value if key in values else value
    return values


def props(scope, unit):
    return parse_properties(ctl(scope, 'show', unit, '--no-pager', PROPERTIES))


def own_unit(path):
    return path.startswith(str(HOME) + '/') or path.startswith('/etc/systemd/system/')


def protected(name):
    return bool(re.search(r'^(?:matrix-spike-|prehlad$|t3code|hermes-gateway$|ssh|tailscale|network|dbus|systemd|docker$|containerd$|user@|karchi-dms|karchi-.*watch)', name, re.I))


def systemd(scope):
    files = ctl(scope, 'list-unit-files', '--type=timer,service', '--no-legend', '--no-pager')
    units = [l.split()[0] for l in files.splitlines() if l.split() and l.split()[0].endswith(('.timer', '.service')) and '@.' not in l.split()[0]]
    # Read all properties in one subprocess, avoiding hundreds of round trips.
    if not units:
        return
    try:
        raw = ctl(scope, 'show', *units, '--no-pager', PROPERTIES)
        blocks = [parse_properties(block) for block in raw.strip().split('\n\n')]
    except RuntimeError:
        # A broken unit must not truncate everything after it in systemctl's output.
        blocks = []
        for unit in units:
            try:
                blocks.append(props(scope, unit))
            except RuntimeError:
                ERRORS.append({'source': 'systemd ' + scope, 'error': 'Nepodarilo sa prečítať jednotku ' + unit})
    byid = {p.get('Id'): p for p in blocks}
    timer_refs = {}
    for p in byid.values():
        if p.get('Id', '').endswith('.timer') and p.get('Unit'):
            timer_refs.setdefault(p['Unit'], set()).add(p['Id'])
    timed_services = {p.get('Unit') for p in blocks if p.get('Id', '').endswith('.timer') and own_unit(p.get('FragmentPath', ''))}
    for p in blocks:
        unit, path = p.get('Id', ''), p.get('FragmentPath', '')
        if not unit or '@.' in unit or (not own_unit(path) and not unit.startswith('karchi-')) or unit in timed_services:
            continue
        f = Path(path)
        if not f.is_file():
            continue
        timer = unit.endswith('.timer')
        service = p.get('Unit') if timer else unit
        sp = byid.get(service) or (props(scope, service) if service else {})
        other_triggers = sorted((timer_refs.get(service, set()) | set(sp.get('TriggeredBy', '').split())) - {unit}) if timer else []
        definition = {'unit': unit, 'scope': scope, 'content': f.read_text(), 'service': service, 'other_triggers': other_triggers}
        service_path = sp.get('FragmentPath', '')
        if timer and service_path and Path(service_path).is_file():
            definition['service_content'] = Path(service_path).read_text()
            for extra in sorted(Path(service_path + '.d').glob('*.conf')):
                definition[str(extra)] = extra.read_text()
        for extra in sorted(Path(str(f) + '.d').glob('*.conf')):
            definition[str(extra)] = extra.read_text()
        for directory in [HOME/'.config/systemd/user'/ (unit+'.d') if scope=='user' else Path('/etc/systemd/system')/(unit+'.d')]:
            for extra in sorted(directory.glob('*.conf')):
                definition[str(extra)] = extra.read_text()
        active, enabled = p.get('ActiveState'), p.get('UnitFileState')
        running = sp.get('ActiveState') == 'active'
        last = sp.get('ExecMainExitTimestamp') or ''
        result = sp.get('Result', '')
        status = 'beží' if running else ('chyba' if result and result != 'success' or sp.get('ActiveState') == 'failed' else 'naplánované' if timer and active == 'active' else 'vypnuté' if active == 'inactive' else 'neznáme')
        if timer and active == 'inactive' and enabled in ('disabled', 'masked'):
            status = 'vypnuté'
        last_status = ('úspech' if result == 'success' else 'chyba') if last else 'neznáme'
        reason = 'Táto služba zabezpečuje prístup alebo samotný Weft.' if protected(unit.removesuffix('.service').removesuffix('.timer')) or protected((service or '').removesuffix('.service')) else ''
        if not own_unit(path):
            reason = 'Jednotku spravuje KarchiOS; odstránenie patrí do jeho konfigurácie.'
        if f.is_symlink():
            reason = 'Definícia je odkaz; spravuje ju inštalátor.'
        # A service with a timer is deleted only together with its timer.
        if not timer and p.get('TriggeredBy'):
            reason = 'Službu spúšťa iná jednotka; odstráň jej časovač.'
        keep_service = bool(other_triggers or not own_unit(service_path) or Path(service_path).is_symlink()) if timer else False
        effect = ('Zastaví a zruší iba tento časovač. Zdieľaná alebo balíkom spravovaná služba a ostatné časovače zostanú.' if keep_service else 'Zastaví a zruší časovač aj jeho vlastnú službu.') if timer else 'Zastaví službu a odstráni jej vlastnú definíciu. Zdrojový program a jeho dáta zostanú.'
        next_run = p.get('NextElapseUSecRealtime') or None
        monotonic = p.get('NextElapseUSecMonotonic', '')
        if timer and not next_run and monotonic not in ('', '0', 'infinity'):
            import time
            factors = {'us': .000001, 'ms': .001, 's': 1, 'min': 60, 'h': 3600, 'd': 86400, 'w': 604800}
            parts = re.findall(r'([\d.]+)(us|ms|min|s|h|d|w)', monotonic)
            if parts:
                seconds = sum(float(n) * factors[u] for n, u in parts)
                next_run = dt.datetime.fromtimestamp(time.time() + seconds - time.monotonic(), dt.timezone.utc).isoformat()
        add('systemd', scope + ':' + unit, p.get('Description') or unit, definition,
            technical=unit, scope=scope, path=path, schedule=redact(p.get('TimersCalendar') or p.get('TimersMonotonic') or 'stále / podľa spúšťača'),
            next_run=next_run, last_run=last or None, last_status=last_status,
            started=(sp.get('ExecMainStartTimestamp') or None) if running else None,
            status=status, command=display_command(sp.get('ExecStart', '')), purpose=redact(p.get('Description')), enabled=enabled,
            delete_reason=reason, delete_effect=effect,
            target={'scope': scope, 'unit': unit, 'service': service, 'path': path, 'keep_service': keep_service})


def parse_cron(text, location, system=False, user=''):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or re.match(r'^[\w]+\s*=', stripped):
            continue
        parts = stripped.split(None, (2 if system else 1) if stripped.startswith('@') else (6 if system else 5))
        n = 1 if stripped.startswith('@') else 5
        if len(parts) <= n + int(system):
            continue
        schedule = ' '.join(parts[:n])
        owner = parts[n] if system else user
        cmd = parts[n + int(system)]
        if location == '/etc/crontab' and 'run-parts' in cmd and '/etc/cron.' in cmd:
            continue
        # Exact original lines identify deletion; group multiple schedules of the same command.
        key = location + ':' + digest({'cmd': cmd, 'owner': owner})
        existing = next((r for r in ROWS if r['kind'] == 'cron' and r['key'] == key), None)
        if existing:
            existing['target']['lines'].append(line)
            existing['schedule'] += '; ' + schedule
            existing['revision'] = digest(existing['target'])
            continue
        try:
            words = shlex.split(display_command(cmd).split(' [ostatné argumenty skryté]')[0])
            name = Path(words[-1]).name
        except (ValueError, IndexError):
            name = 'cron'
        target = dict(location=location, lines=[line], owner=owner)
        add('cron', key, name, target, technical=name, schedule=schedule, next_run=None, last_run=None, last_status='neznáme', status='naplánované',
            purpose='Pravidelný príkaz; cron neukladá výsledok behu.', command=display_command(cmd),
            delete_reason='', delete_effect='Odstráni tieto termíny z cronu. Prípadný rozbehnutý proces, skript aj jeho dáta zostanú.', target=target)


def crons():
    import shutil
    installed = bool(shutil.which('crontab'))
    if installed:
        p = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=10)
        if p.returncode and 'no crontab' not in p.stderr.lower():
            raise RuntimeError('crontab nie je čitateľný')
        parse_cron(p.stdout, 'user', user=str(os.getuid()))
    for f in [Path('/etc/crontab'), *sorted(Path('/etc/cron.d').glob('*'))]:
        if f.is_file() and not f.name.startswith('.'):
            # The OS owns packaged definitions; only hand-installed cron.d definitions count.
            owner = next((cmd for cmd in [['dpkg-query','-S'], ['pacman','-Qo'], ['rpm','-qf']] if shutil.which(cmd[0])), None)
            if f != Path('/etc/crontab') and owner:
                if subprocess.run(owner + [str(f)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    continue
            parse_cron(f.read_text(), str(f), system=True)
    if installed and os.getuid() != 0:
        root = subprocess.run(['sudo', '-n', 'crontab', '-l'], capture_output=True, text=True, timeout=8)
        if root.returncode == 0:
            parse_cron(root.stdout, 'root', user='0')
        elif 'no crontab' not in root.stderr.lower():
            ERRORS.append({'source':'root cron', 'error':'Nedostatočné oprávnenia; root crontab nebol prečítaný.'})


def t3():
    path = HOME/'.t3/userdata/statev2.sqlite'
    if not path.exists():
        return
    c = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    for row in c.execute('SELECT * FROM scheduled_tasks'):
        r = dict(row)
        if r.get('deleted_at'):
            continue
        model = json.loads(r.get('model_selection_json') or '{}')
        sch = json.loads(r.get('schedule_json') or '{}')
        ident = r.get('task_id') or r.get('id') or r.get('scheduled_task_id')
        if not ident:
            raise RuntimeError('T3 schéma nemá identifikátor úlohy')
        definition = {k:r.get(k) for k in ['task_id','id','scheduled_task_id','title','prompt','schedule_json','model_selection_json','enabled','project_id']}
        last = r.get('last_run_status')
        add('t3', ident, r['title'], definition, technical=ident,
            schedule=json.dumps(sch,ensure_ascii=False), next_run=r.get('next_run_at'), last_run=r.get('last_run_at'),
            last_status={'succeeded':'úspech','completed':'úspech','failed':'chyba','running':'beží','interrupted':'prerušené','cancelled':'zrušené'}.get(last,'neznáme'),
            status='vypnuté' if not r['enabled'] else 'chyba' if last=='failed' else 'beží' if last=='running' else 'dokončené' if sch.get('type')=='once' and last in ('succeeded','completed') and not r.get('next_run_at') else 'naplánované',
            purpose='Plánovaná úloha T3', command='', model=redact(model.get('model')), provider=redact(model.get('provider') or model.get('instanceId') or ''),
            delete_reason='', delete_effect='Zruší plánovanú úlohu cez T3. Existujúce vlákna a súbory zostanú.', target={'id':ident})
    c.close()


def hermes_defaults():
    f=HOME/'.hermes/config.yaml'
    result={}
    if not f.exists():
        return result
    inside=False
    for line in f.read_text().splitlines():
        if line.startswith('model:'):
            inside=True
            continue
        if inside and line and not line.startswith((' ', '#')):
            break
        if inside:
            match=re.match(r"^  (default|provider):\s*['\"]?([\w./:-]+)",line)
            if match:
                result[match[1]]=match[2]
    return result


def hermes():
    f = HOME/'.hermes/cron/jobs.json'
    if not f.exists():
        return
    d = json.loads(f.read_text())
    defaults=hermes_defaults()
    jobs = d.get('jobs',[]) if isinstance(d,dict) else d
    for r in jobs:
        definition = {k:r.get(k) for k in ['id','name','prompt','script','schedule','model','provider','enabled','workdir']}
        last = r.get('last_status')
        add('hermes', r['id'], r.get('name') or r['id'], definition, technical=r['id'],
            schedule=r.get('schedule_display') or r.get('schedule',{}).get('display') or json.dumps(r.get('schedule',{})),
            next_run=r.get('next_run_at'), last_run=r.get('last_run_at'),
            last_status={'ok':'úspech','error':'chyba','failed':'chyba'}.get(last,'neznáme'),
            status='vypnuté' if not r.get('enabled',True) else 'chyba' if last in ['error','failed'] else 'naplánované',
            purpose='Pravidelná úloha Hermesa', command=display_command(r.get('script') or ''), model=redact(r.get('model') or defaults.get('default')), provider=redact(r.get('provider') or defaults.get('provider')), ai_hint='nie' if r.get('no_agent') else 'áno',
            delete_reason='', delete_effect='Zruší úlohu Hermesa, jej prípadný živý beh aj uložené výstupy tejto úlohy. Zdrojový skript zostane.', target={'id':r['id']})


def docker():
    # Do not treat an absent Docker as a failed source.
    import shutil
    if not shutil.which('docker'):
        return
    prefix = ['docker']
    p = subprocess.run(prefix+['ps','-aq'],text=True,capture_output=True,timeout=8)
    if p.returncode:
        prefix = ['sudo','-n','docker']
        ids = run(prefix+['ps','-aq']).split()
    else:
        ids = p.stdout.split()
    if not ids:
        return
    for r in json.loads(run(prefix+['inspect', *ids])):
        name = r['Name'].lstrip('/')
        labels = r.get('Config',{}).get('Labels') or {}
        compose = labels.get('com.docker.compose.project')
        state = r.get('State',{})
        definition={'id':r['Id'],'image':r['Config'].get('Image'),'created':r.get('Created')}
        add('docker',r['Id'], name, definition, technical=name, schedule='stále / podľa politiky reštartu', next_run=None,
            last_run=state.get('FinishedAt') if not state.get('Running') else state.get('StartedAt'),
            last_status='chyba' if state.get('ExitCode') else 'beží' if state.get('Running') else 'neznáme',
            status='beží' if state.get('Running') else 'chyba' if state.get('ExitCode') else 'vypnuté',
            purpose='Kontajner '+redact(r['Config'].get('Image')), command=redact(r['Config'].get('Image')),
            delete_reason='Kontajner spravuje Compose; odstránenie patrí do jeho projektu.' if compose else 'Súčasť infraštruktúry Weftu.' if protected(name) else '',
            delete_effect='Zastaví a odstráni kontajner. Obraz, zväzky a pripojené dáta zostanú.', target={'id':r['Id'],'prefix':prefix})


def collect():
    ROWS.clear()
    ERRORS.clear()
    for name, fn in [('systemd user',lambda:systemd('user')),('systemd system',lambda:systemd('system')),('cron',crons),('T3',t3),('Hermes',hermes),('Docker',docker)]:
        source(name,fn)
    return {'rows':ROWS,'errors':ERRORS,'collected_at':dt.datetime.now(dt.timezone.utc).isoformat()}


def main():
    try:
        request=json.load(sys.stdin)
        if request.get('action', 'collect') != 'collect':
            raise ValueError('Prehľad je iba na čítanie.')
        result=collect()
    except Exception as e:
        result={'error':redact(str(e)), 'type':type(e).__name__}
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()

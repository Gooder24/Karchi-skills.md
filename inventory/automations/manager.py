"""Read-only Weft automation endpoint, hosted by the existing Prehľad process."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import threading
import time

HERE=Path(__file__).parent
CACHE=Path.home()/'.cache/prehlad/automations.json'
MASTERS=Path.home()/'.cache/prehlad/ssh'
HOSTS=['asus','dell','e540','x270','vps']
lock=threading.RLock()
refresh_lock=threading.Lock()
state={'hosts':{},'refreshing':False}


def ssh_args(host, script, master_dir):
    # Shared SSH connections keep the 5-second live samples cheap; vps is reachable only through x270.
    code=(HERE/script).read_text()
    command=shlex.join(['python3','-c',code])
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=6','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',
         '-o','ControlMaster=auto','-o','ControlPersist=120']
    if host=='asus':
        return ['python3','-c',code]
    if host=='vps':
        return ssh+['-o',f'ControlPath={master_dir}/%C','x270',shlex.join(ssh+['-o','ControlPath=/tmp/prehlad-cm-%C','root@81.2.239.39',command])]
    return ssh+['-o',f'ControlPath={master_dir}/%C',host,command]


def remote(host, request):
    MASTERS.mkdir(parents=True,exist_ok=True)
    p=subprocess.run(ssh_args(host,'agent.py',MASTERS),input=json.dumps(request),capture_output=True,text=True,timeout=100)
    if p.returncode:
        raise RuntimeError('Stroj neodpovedá alebo odmietol prístup.')
    try:
        data=json.loads(p.stdout)
    except ValueError:
        raise RuntimeError('Stroj vrátil neplatné údaje.')
    if data.get('error'):
        raise RuntimeError(data['error'])
    return data


def enrich(host,row):
    # Reuse the established descriptions, but never infer a subscription from a process name alone.
    spec=importlib.util.spec_from_file_location('known_inventory',HERE.parent/'inventory.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    name=row.get('technical',row['name']).removesuffix('.service').removesuffix('.timer')
    hit=m.classify(host,{'name':name}) or m.classify(host,{'name':row['name']})
    row['ai'],row['subscription']='neznáme','neznáme'
    row.setdefault('model','neznáme')
    if hit:
        ai,sub,model,purpose=hit
        row.update(ai=ai,subscription=sub or 'bez predplatného',purpose=purpose)
        if model:
            row['model']=model
    if row['kind'] in ['t3','hermes']:
        row['ai']=row.get('ai_hint','áno')
        provider=row.get('provider','')
        # Configuration is evidence for the provider, never for the billing account.
        row['subscription']='bez predplatného' if row['ai']=='nie' else (hit[1] if hit else 'účet nie je v konfigurácii')
    if name=='hermes-gateway':
        row.update(ai='spúšťa',purpose='Hermes: osobný asistent vo Wefte',subscription='podľa konfigurácie Hermesa')
    if row['kind']=='cron':
        row['schedule']='; '.join(m.when_text({'kind':'cron','when':part}) for part in row['schedule'].split('; '))
    elif row['kind']=='systemd' and row['technical'].endswith('.timer'):
        row['schedule']=m.when_text({'kind':'timer','when':row['schedule']})
    from zoneinfo import ZoneInfo
    import re
    if row['kind']=='hermes':
        if re.fullmatch(r'[\d*/, -]+', row['schedule']) and len(row['schedule'].split())==5:
            row['schedule']=m.when_text({'kind':'cron','when':row['schedule']})
        interval=re.fullmatch(r'every (\d+)m',row['schedule'])
        if interval: row['schedule']='každých '+interval[1]+' min'
    if row['kind']=='systemd' and row.get('schedule','').startswith('{'):
        # Monotonic timers: '{ OnUnitInactiveUSec=5min ; next_elapse=... }'.
        words={'UnitInactive':'každých {} od konca behu','UnitActive':'každých {}','Boot':'{} po štarte','Startup':'{} po štarte','Active':'{} po zapnutí'}
        parts=[words.get(k,'{}').format(re.sub(r'(\d)([a-z])',r'\1 \2',v)) for k,v in re.findall(r'On(\w+?)USec=([^ ;}]+)',row['schedule'])]
        if parts: row['schedule']=', '.join(parts)
    row['schedule']={'*-*-* *:00:00':'každú hodinu','*-*-* *:*:00':'každú minútu'}.get(row.get('schedule'),row.get('schedule'))
    if row.get('schedule'): row['schedule']=re.sub(r'(\d)(min|s|h|d)\b',r'\1 \2',row['schedule'])
    hourly=re.fullmatch(r'\*-\*-\* (\d\d)\.\.(\d\d):(\d\d):00',row.get('schedule',''))
    if hourly:
        row['schedule']=f'každú hodinu od {hourly[1]}:{hourly[3]} do {hourly[2]}:{hourly[3]}'
    for field in ['last_run','next_run','started']:
        raw=row.get(field) or ''
        match=re.search(r'(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)',raw)
        if match:
            row[field]=dt.datetime.fromisoformat(match[1]+'T'+match[2]).replace(tzinfo=ZoneInfo('UTC') if 'UTC' in raw else ZoneInfo('Europe/Bratislava')).isoformat()
    row['device']=host
    row['id']=hashlib.sha256((host+'\0'+row['kind']+'\0'+row['key']).encode()).hexdigest()
    return row


def collect_host(host):
    d=remote(host,{'action':'collect'})
    d['rows']=[enrich(host,r) for r in d['rows']]
    d['offline']=False
    return d


def refresh():
    if not refresh_lock.acquire(blocking=False):
        return
    with lock:
        state['refreshing']=True
    try:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures={pool.submit(collect_host,h):h for h in HOSTS}
            for f in as_completed(futures):
                host=futures[f]
                try:
                    d=f.result()
                except Exception as e:
                    with lock:
                        d=dict(state['hosts'].get(host,{'rows':[],'collected_at':None,'errors':[]}))
                    d.update(offline=True,error=str(e)[:160])
                with lock:
                    state['hosts'][host]=d
        CACHE.parent.mkdir(parents=True,exist_ok=True)
        temp=CACHE.with_suffix('.tmp')
        with lock:
            payload=json.dumps(state['hosts'],ensure_ascii=False)
        temp.write_text(payload);temp.chmod(0o600);temp.replace(CACHE)
    finally:
        with lock:
            state['refreshing']=False
        refresh_lock.release()


def start():
    if CACHE.exists():
        try:
            state['hosts']=json.loads(CACHE.read_text())
        except (ValueError,OSError):
            pass
    def loop():
        while True:
            try:
                refresh()
            except Exception:
                # One failed refresh must not kill the collector thread.
                pass
            time.sleep(300)
    threading.Thread(target=loop,daemon=True).start()
    start_live()


# Live load. Samples every LIVE_EVERY seconds while a page asks for it, otherwise every IDLE_EVERY.
LIVE_EVERY,IDLE_EVERY,HISTORY=5,60,72
live={'hosts':{},'viewed':0.0}
live_lock=threading.Lock()
sampling={}


def sample_host(host):
    try:
        p=subprocess.run(ssh_args(host,'stats.py',MASTERS),capture_output=True,text=True,timeout=20)
        if p.returncode:
            raise RuntimeError('Stroj neodpovedá.')
        now=json.loads(p.stdout)
    except Exception as e:
        with live_lock:
            h=live['hosts'].setdefault(host,{'history':[]})
            h.update(offline=True,error=str(e)[:120],checked=time.time())
        return
    with live_lock:
        h=live['hosts'].setdefault(host,{'history':[]})
        prev=h.get('raw')
        if prev:
            busy=now['cpu'][0]-prev['cpu'][0];total=now['cpu'][1]-prev['cpu'][1]
            h['cpu']=round(100*busy/total,1) if total>0 else 0.0
            h['history']=(h['history']+[[round(now['time']),h['cpu']]])[-HISTORY:]
            wall=(now['time']-prev['time'])*1e6*(now['cores'] or 1)
            h['procs']={k:{'cpu':round(100*max(0,v[0]-prev['cgroups'].get(k,[v[0]])[0])/wall,1) if wall>0 else 0.0,'mem':v[1]} for k,v in now['cgroups'].items()}
        else:
            h['procs']={k:{'cpu':None,'mem':v[1]} for k,v in now['cgroups'].items()}
        h.update(raw=now,offline=False,error=None,checked=now['time'],
                 cores=now['cores'],cpu_model=now['cpu_model'],os=now['os'],load=now['load'],uptime=now['uptime'],
                 mem=now['mem'],disk=now['disk'],temp=now['temp'],battery=now['battery'])


def sample_all():
    for host in HOSTS:
        with live_lock:
            busy=sampling.get(host)
            if busy:
                continue
            sampling[host]=True
        def run(host=host):
            try:
                sample_host(host)
            finally:
                with live_lock:
                    sampling[host]=False
        threading.Thread(target=run,daemon=True).start()


def start_live():
    def loop():
        last=0.0
        while True:
            every=LIVE_EVERY if time.time()-live['viewed']<20 else IDLE_EVERY
            if time.time()-last>=every:
                last=time.time();sample_all()
            time.sleep(1)
    threading.Thread(target=loop,daemon=True).start()


def live_data():
    live['viewed']=time.time()
    with live_lock:
        hosts=json.loads(json.dumps({k:{f:v for f,v in h.items() if f!='raw'} for k,h in live['hosts'].items()}))
        rows=[r for d in state['hosts'].values() for r in d.get('rows',[])]
    procs={}
    for r in rows:
        if r['kind']=='systemd':
            unit=r.get('technical','')
            unit=unit[:-6]+'.service' if unit.endswith('.timer') else unit
            key=r.get('scope','system')+':'+unit
        elif r['kind']=='docker':
            key='docker-'+r['key']+'.scope'
        else:
            continue
        hit=hosts.get(r['device'],{}).get('procs',{}).get(key)
        if hit:
            procs[r['id']]=hit
    for h in hosts.values():
        h.pop('procs',None)
    return {'hosts':hosts,'procs':procs,'now':time.time()}


def public_data():
    with lock:
        hosts=json.loads(json.dumps(state['hosts']))
        refreshing=state['refreshing']
    rows=[]
    summary=[]
    now=time.time()
    for host in HOSTS:
        d=hosts.get(host,{})
        collected=d.get('collected_at')
        try:
            stale=now-dt.datetime.fromisoformat(collected).timestamp()>900
        except (TypeError,ValueError):
            stale=True
        summary.append({'device':host,'collected_at':collected,'offline':d.get('offline',False),'stale':stale,'error':d.get('error'), 'errors':d.get('errors',[])})
        for row in d.get('rows',[]):
            for private in ['target','revision','delete_reason','delete_effect']:
                row.pop(private,None)
            row['collected_at']=collected
            row['stale']=stale or d.get('offline',False)
            rows.append(row)
    return {'rows':rows,'hosts':summary,'refreshing':refreshing}



def handle(handler,path,method):
    if not path.startswith('/_automations/'):
        return False
    if handler.headers.get('X-Weft-Route') != '1':
        handler.send(404, '{"error":"Nenájdené"}')
        return True
    if method != 'GET':
        handler.send(405, '{"error":"Prehľad je iba na čítanie."}')
        return True
    if path == '/_automations/stats':
        handler.send(200,json.dumps(live_data(),ensure_ascii=False))
        return True
    if path != '/_automations/data':
        handler.send(404, '{"error":"Nenájdené"}')
        return True
    # Caddy serves this only on the tailnet address and localhost, so a read needs no login.
    handler.send(200,json.dumps(public_data(),ensure_ascii=False))
    return True

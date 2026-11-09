"""Authenticated Weft automation endpoints, hosted by the existing Prehľad process."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
import threading
import time
import urllib.request

HERE=Path(__file__).parent
CACHE=Path.home()/'.cache/prehlad/automations.json'
HOSTS=['asus','dell','e540','x270','vps']
lock=threading.RLock()
refresh_lock=threading.Lock()
tickets={}
state={'hosts':{},'refreshing':False}


def remote(host, request):
    code=(HERE/'agent.py').read_text()
    command=shlex.join(['python3','-c',code])
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=6','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2']
    if host=='asus':
        args=['python3','-c',code]
    elif host=='vps':
        args=ssh+['x270',shlex.join(ssh+['root@81.2.239.39',command])]
    else:
        args=ssh+[host,command]
    p=subprocess.run(args,input=json.dumps(request),capture_output=True,text=True,timeout=100)
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
    hourly=re.fullmatch(r'\*-\*-\* (\d\d)\.\.(\d\d):(\d\d):00',row.get('schedule',''))
    if hourly:
        row['schedule']=f'každú hodinu od {hourly[1]}:{hourly[3]} do {hourly[2]}:{hourly[3]}'
    for field in ['last_run','next_run']:
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


def auth(handler):
    authorization=handler.headers.get('Authorization','')
    if not authorization.startswith('Bearer ') or len(authorization)>8000:
        raise PermissionError('Prihlás sa do Weftu.')
    req=urllib.request.Request('http://127.0.0.1:8008/_matrix/client/v3/account/whoami',headers={'Authorization':authorization})
    try:
        with urllib.request.urlopen(req,timeout=6) as r:
            who=json.load(r)
    except Exception:
        raise PermissionError('Prihlásenie sa nepodarilo overiť. Otvor Weft a prihlás sa.')
    if who.get('user_id')!='@karchi:asus-vivobook-x1504v.taila3702d.ts.net':
        raise PermissionError('Tento prehľad patrí Karchimu.')
    return hashlib.sha256(authorization.encode()).hexdigest()


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
            row.pop('target',None)
            row['collected_at']=collected
            row['stale']=stale or d.get('offline',False)
            rows.append(row)
    return {'rows':rows,'hosts':summary,'refreshing':refreshing}


def resolve(payload):
    ident=payload.get('id')
    with lock:
        for host,d in state['hosts'].items():
            for row in d.get('rows',[]):
                if row['id']==ident:
                    return host,dict(row)
    raise ValueError('Položka už nie je v zozname. Obnov prehľad.')


def handle(handler,path,method):
    if not path.startswith('/_automations/'):
        return False
    if handler.headers.get('X-Weft-Route') != '1':
        handler.send(404, '{"error":"Nenájdené"}')
        return True
    def send(code,data):
        handler.send(code,json.dumps(data,ensure_ascii=False))
    try:
        subject=auth(handler)
        if method=='GET' and path=='/_automations/data':
            send(200,public_data());return True
        if method!='POST' or handler.headers.get('X-Weft-Automations')!='1':
            raise PermissionError('Požiadavka neprišla z prehľadu Weftu.')
        # Custom header + no CORS response enforce same-origin browser requests.
        origin=handler.headers.get('Origin')
        if origin and origin not in ['https://100.110.180.15:8443','http://127.0.0.1:8080','http://127.0.0.1:18080']:
            raise PermissionError('Nepovolený pôvod požiadavky.')
        size=int(handler.headers.get('Content-Length','0'))
        if not 0<size<=4096:
            raise ValueError('Neplatná veľkosť požiadavky.')
        payload=json.loads(handler.rfile.read(size))
        if path=='/_automations/refresh':
            threading.Thread(target=refresh,daemon=True).start()
            send(202,{'ok':True});return True
        if path not in ['/_automations/preview','/_automations/delete']:
            send(404,{'error':'Nenájdené'});return True
        host,row=resolve(payload)
        if row['revision']!=payload.get('revision'):
            raise ValueError('Položka sa zmenila. Obnov zoznam.')
        if row.get('delete_reason'):
            raise ValueError(row['delete_reason'])
        if path=='/_automations/preview':
            # Refresh the selected host before issuing the confirmation ticket.
            fresh=collect_host(host)
            current=next((r for r in fresh['rows'] if r['id']==row['id']),None)
            if not current or current['revision']!=row['revision']:
                raise ValueError('Definícia sa zmenila. Obnov zoznam.')
            if current.get('delete_reason'):
                raise ValueError(current['delete_reason'])
            nonce=secrets.token_urlsafe(24)
            with lock:
                for k in list(tickets):
                    if tickets[k]['expires']<time.time(): del tickets[k]
                tickets[nonce]={'subject':subject,'id':row['id'],'revision':row['revision'],'expires':time.time()+120}
            send(200,{'ticket':nonce,'name':row['name'],'device':host,'effect':row['delete_effect']});return True
        with lock:
            ticket=tickets.pop(payload.get('ticket',''),None)
        if not ticket or ticket['expires']<time.time() or any(ticket[k]!=v for k,v in [('subject',subject),('id',row['id']),('revision',row['revision'])]):
            raise ValueError('Potvrdenie vypršalo. Otvor mazanie znova.')
        # Serialize against scans, so an older scan cannot resurrect a deleted row.
        with refresh_lock:
            remote(host,{'action':'delete','kind':row['kind'],'key':row['key'],'revision':row['revision']})
            with lock:
                d=state['hosts'].get(host,{})
                d['rows']=[r for r in d.get('rows',[]) if r['id']!=row['id']]
        threading.Thread(target=refresh,daemon=True).start()
        send(200,{'ok':True})
    except PermissionError as e:
        send(403,{'error':str(e)})
    except (ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        send(409,{'error':str(e) if not isinstance(e,subprocess.TimeoutExpired) else 'Stroj neodpovedal včas. Stav odstránenia je neznámy; obnov prehľad.'})
    except Exception:
        send(500,{'error':'Operácia zlyhala. Obnov zoznam a skús znova.'})
    return True

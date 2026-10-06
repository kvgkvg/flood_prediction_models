#!/usr/bin/env python3
"""Download only the locked-period IFS rain chunks, resumably and quota-bounded."""
from __future__ import annotations
from datetime import date, timedelta
from pathlib import Path
import argparse, gzip, json, math, time
import pandas as pd
import requests
from floodrisk.cities import CITIES
from download_rain import wait_for_budget

URL='https://archive-api.open-meteo.com/v1/archive'
ROOT=Path('data/raw/rain_source_experiments/ecmwf_ifs')
STATE=Path('data/raw/open_meteo/.task8_locked_weight.json')
CAP=1200
UA='floodrisk-hackathon/0.1 (locked-period IFS precipitation; contact unavailable)'

def points(city):
    w,s,e,n=CITIES[city].bbox; ny,nx=(3,3) if city=='ho_chi_minh' else (2,3)
    return [(float(y),float(x)) for y in __import__('numpy').linspace(s,n,ny) for x in __import__('numpy').linspace(w,e,nx)]

def fetch(city,year,end,pilot=False):
    a=date(year,1,1); b=min(date(year,12,31),end); locs=points(city)
    base=ROOT/city/str(year); pq=base.with_suffix('.parquet'); meta=base.with_suffix('.meta.json'); raw=base.with_suffix('.json.gz')
    if pq.exists() and meta.exists():
        try:
            d=pd.read_parquet(pq,columns=['time','precipitation'])
            if len(d) and d.precipitation.notna().any():return {'cached':True,'rows':len(d),'weight':0}
        except Exception:pass
    w=len(locs)*math.ceil(((b-a).days+1)/14)
    try:s=json.loads(STATE.read_text())
    except Exception:s={'weight_used':0,'cap':CAP}
    if s.get('weight_used',0)+w>CAP:raise RuntimeError(f'locked rain cap exceeded: {s.get("weight_used",0)}+{w}>{CAP}')
    # Reserve our task-local cap before the provider-wide hourly/daily quota.
    s['weight_used']=s.get('weight_used',0)+w;s['cap']=CAP;s['last_reserved']=w
    STATE.parent.mkdir(parents=True,exist_ok=True);tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(s,indent=2));tmp.replace(STATE)
    wait_for_budget(w)
    params={'latitude':','.join(f'{y:.6f}' for y,x in locs),'longitude':','.join(f'{x:.6f}' for y,x in locs),
            'start_date':a.isoformat(),'end_date':b.isoformat(),'hourly':'precipitation','timezone':'Asia/Ho_Chi_Minh','models':'ecmwf_ifs'}
    session=requests.Session();session.headers.update({'User-Agent':UA,'Accept':'application/json'})
    time.sleep(1.1);r=session.get(URL,params=params,timeout=180)
    if r.status_code==429:raise RuntimeError(f'HTTP 429; stopping immediately: {r.url} body={r.text[:1200]}')
    try:r.raise_for_status()
    except requests.RequestException as e:raise RuntimeError(f'HTTP {r.status_code} {r.url}: {r.text[:1200]}') from e
    payload=r.json();items=payload if isinstance(payload,list) else [payload]
    if len(items)!=len(locs):raise RuntimeError(f'expected {len(locs)} location results, got {len(items)} from {r.url}')
    parts=[];resolved=[]
    for i,obj in enumerate(items):
        h=obj.get('hourly') or {}; ts=h.get('time',[]); vals=h.get('precipitation',[])
        if not ts or len(ts)!=len(vals) or pd.isna(pd.to_numeric(vals,errors='coerce')).all():raise RuntimeError(f'empty/null precipitation item {i}: {r.url}')
        lat=float(obj['latitude']);lon=float(obj['longitude'])
        parts.append(pd.DataFrame({'time':pd.to_datetime(ts),'precipitation':pd.to_numeric(vals,errors='coerce'),'latitude_returned':lat,'longitude_returned':lon,'requested_latitude':locs[i][0],'requested_longitude':locs[i][1],'model':'ecmwf_ifs'}))
        resolved.append({'latitude':lat,'longitude':lon,'elevation':obj.get('elevation'),'grid_resolution':obj.get('grid_resolution'),'model':obj.get('model'),'hourly_units':obj.get('hourly_units')})
    out=pd.concat(parts,ignore_index=True)
    base.parent.mkdir(parents=True,exist_ok=True);out.to_parquet(pq,index=False)
    with gzip.open(raw,'wt',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'))
    meta.write_text(json.dumps({'city':city,'model':'ecmwf_ifs','start_date':str(a),'end_date':str(b),'url':r.url,'status':r.status_code,'request_points':locs,'returned_points':resolved,'rows':len(out),'weight':w,'response_keys':list(items[0]),'license':'Open-Meteo data attribution required; source dataset terms apply'},indent=2))
    return {'cached':False,'rows':len(out),'weight':w,'returned':resolved}

def main(pilot=False):
    end=date.today()-timedelta(days=1);plan=[('ho_chi_minh',2025),('da_nang',2025),('ho_chi_minh',2026),('da_nang',2026)]
    if pilot:plan=plan[:1]
    for i,(city,year) in enumerate(plan,1):
        print(f'[{i}/{len(plan)}] IFS {city} {year} ending {min(date(year,12,31),end)}',flush=True)
        result=fetch(city,year,end,pilot);print(json.dumps({'city':city,'year':year,**result},default=str),flush=True)
    print(STATE.read_text(),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');main(p.parse_args().pilot)

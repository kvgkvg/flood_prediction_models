#!/usr/bin/env python3
"""Quota-aware, resumable Open-Meteo archive precipitation downloader.

No API call is made on import. Default model is ERA5; --model ecmwf_ifs is
available as a separate later pass. Local hourly/daily weighted budgets persist.
"""
from __future__ import annotations
import argparse, json, math, time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import requests
from floodrisk.cities import CITIES

API = 'https://archive-api.open-meteo.com/v1/archive'
STATE = Path('data/raw/open_meteo/.quota_state.json')
UA = 'floodrisk-hackathon/0.1 (Open-Meteo historical data client)'
LIMIT_HOUR, LIMIT_DAY = 4000, 9000
MODELS = {'era5': (0.25, date(2002,1,1)), 'ecmwf_ifs': (0.08, date(2017,1,1))}

def request_points(bbox, model='era5'):
    """Candidate grid centers at native nominal spacing; API returned centers dedupe cells."""
    w,s,e,n=bbox; step=MODELS[model][0]
    # For ERA5, exact quarter-degree grid. IFS is ~9 km; use ~0.08 degrees.
    if model == 'era5':
        def axis(lo,hi):
            # Cell centers up to half a cell beyond a bbox edge still intersect it.
            k=math.ceil((lo-step/2)/step-1e-10); upper=hi+step/2
            return [round(k*step+i*step,4) for i in range(int(math.floor((upper-k*step)/step+1e-9))+1)]
        ys=axis(s,n); xs=axis(w,e)
    else:
        lat0=math.ceil((s-step/2)/step-1e-10)*step; lonstep=step/max(.1,math.cos(math.radians((s+n)/2)))
        ys=[]; v=lat0
        while v<=n+step/2: ys.append(round(v,4)); v+=step
        lon0=math.ceil((w-lonstep/2)/lonstep-1e-10)*lonstep; xs=[]; v=lon0
        while v<=e+lonstep/2: xs.append(round(v,4)); v+=lonstep
    return [(y,x) for y in ys for x in xs]

def weight(start, end, locations=1, variables=1):
    return locations*math.ceil(((end-start).days+1)/14)*math.ceil(variables/10)

def quota_state(now=None):
    now=now or time.time(); dt=datetime.fromtimestamp(now,timezone.utc)
    hour=int(dt.replace(minute=0,second=0,microsecond=0).timestamp())
    day=int(dt.replace(hour=0,minute=0,second=0,microsecond=0).timestamp())
    try: x=json.loads(STATE.read_text())
    except (OSError,ValueError): x={}
    if x.get('hour_epoch') != hour: x.update(hour_epoch=hour,hour_weight=0)
    if x.get('day_epoch') != day: x.update(day_epoch=day,day_weight=0)
    return x

def persist_state(x):
    STATE.parent.mkdir(parents=True,exist_ok=True); tmp=STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(x,sort_keys=True)); tmp.replace(STATE)

def wait_for_budget(w, now_fn=time.time, sleep_fn=time.sleep):
    while True:
        now=now_fn(); x=quota_state(now)
        if x['hour_weight']+w<=LIMIT_HOUR and x['day_weight']+w<=LIMIT_DAY:
            x['hour_weight']+=w; x['day_weight']+=w; persist_state(x); return
        dt=datetime.fromtimestamp(now,timezone.utc)
        until=(dt.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)).timestamp()+1
        if x['day_weight']+w>LIMIT_DAY:
            until=(dt.replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1)).timestamp()+1
        sleep_fn(max(1,until-now))

def valid_chunk(path):
    try:
        d=pd.read_parquet(path,columns=['precipitation','latitude_returned','longitude_returned'])
        return len(d)>0 and d.precipitation.notna().any() and d.latitude_returned.notna().all() and d.longitude_returned.notna().all()
    except Exception: return False

def chunks(end, model):
    start=max(date(2002,1,1),MODELS[model][1])
    # All cities' recent years first, then historical years 2002-2009.
    recent=[]; old=[]
    for slug, city in CITIES.items():
        for lat,lon in request_points(city.bbox,model):
            for year in range(start.year,end.year+1):
                a=max(start,date(year,1,1)); b=min(end,date(year,12,31))
                dest=Path('data/raw/open_meteo' if model=='era5' else 'data/raw/open_meteo_ecmwf_ifs')/slug/f'{lat:.4f}_{lon:.4f}_{year}.parquet'
                item=(slug,lat,lon,a,b,dest)
                (recent if year>=2010 else old).append(item)
    return recent+old

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--model',choices=MODELS,default='era5'); args=ap.parse_args()
    model=args.model; end=date.today()-timedelta(days=1); session=requests.Session(); session.headers.update({'User-Agent':UA,'Accept':'application/json'})
    print(f'model={model.upper()} nominal_native_resolution={MODELS[model][0]} degrees; variable=precipitation; API-returned latitude/longitude are stored for actual-cell deduplication',flush=True)
    cell_owner={slug:{} for slug in CITIES}; resolved={}; rows=chunks(end,model)
    for i,(slug,lat,lon,a,b,path) in enumerate(rows,1):
        key=(slug,lat,lon)
        if key in resolved and cell_owner[slug].get(resolved[key]) != key:
            print(f'chunk {i}/{len(rows)} {slug} ({lat:.4f},{lon:.4f}) {a}..{b}: duplicate returned grid cell {resolved[key]}; skipped',flush=True)
            continue
        if path.exists() and valid_chunk(path):
            cached=pd.read_parquet(path,columns=['latitude_returned','longitude_returned'])
            returned=(round(float(cached.latitude_returned.iloc[0]),5),round(float(cached.longitude_returned.iloc[0]),5))
            owner=cell_owner[slug].get(returned)
            if owner is not None and owner!=key:
                resolved[key]=returned
                print(f'chunk {i}/{len(rows)} {slug} ({lat:.4f},{lon:.4f}) {a}..{b}: cached duplicate cell {returned}; skipped',flush=True)
                continue
            cell_owner[slug][returned]=key; resolved[key]=returned
        else:
            w=weight(a,b)
            wait_for_budget(w)
            params={'latitude':lat,'longitude':lon,'start_date':a.isoformat(),'end_date':b.isoformat(),'hourly':'precipitation','timezone':'Asia/Ho_Chi_Minh','models':model}
            while True:
                try: response=session.get(API,params=params,timeout=180)
                except requests.RequestException as e:
                    print(f'chunk {i}/{len(rows)} {slug} {lat},{lon} {a}..{b}: request error {e}; retry in 60s',flush=True); time.sleep(60); wait_for_budget(w); continue
                if response.status_code==429:
                    state=quota_state(); state['hour_weight']=LIMIT_HOUR; persist_state(state)
                    now=time.time(); dt=datetime.fromtimestamp(now,timezone.utc); target=(dt.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)).timestamp()+1
                    state['day_weight']=max(0,state.get('day_weight',0)-w); persist_state(state)
                    delay=max(1,target-now); print(f'chunk {i}/{len(rows)} HTTP 429; sleeping {delay:.0f}s to next UTC hour; {response.text[:500]}',flush=True); time.sleep(delay); wait_for_budget(w); continue
                if response.status_code in (502,503,504):
                    delay=30; print(f'chunk {i}/{len(rows)} HTTP {response.status_code}; retry in {delay}s: {response.text[:500]}',flush=True); time.sleep(delay); wait_for_budget(w); continue
                try: response.raise_for_status()
                except requests.RequestException as e:
                    print(f'chunk {i}/{len(rows)} FAILED {response.url}: {e}; body={response.text[:1200]}',flush=True); raise
                obj=response.json(); record=(obj[0] if isinstance(obj,list) else obj)
                hourly=record.get('hourly') or {}; frame=pd.DataFrame(hourly)
                if frame.empty or 'precipitation' not in frame or frame.precipitation.isna().all():
                    print(f'chunk {i}/{len(rows)} INVALID (empty/null); not writing; retry in 60s',flush=True); time.sleep(60); wait_for_budget(w); continue
                returned=(round(float(record.get('latitude')),5),round(float(record.get('longitude')),5))
                owner=cell_owner[slug].get(returned)
                if owner is not None and owner!=key:
                    resolved[key]=returned
                    print(f'chunk {i}/{len(rows)} duplicate returned cell {returned}; discarded',flush=True); break
                cell_owner[slug][returned]=key; resolved[key]=returned
                frame.insert(0,'time',pd.to_datetime(frame.pop('time'))); frame['latitude_returned']=returned[0]; frame['longitude_returned']=returned[1]
                frame['requested_latitude']=lat; frame['requested_longitude']=lon; frame['model']=model.upper(); frame['nominal_grid_resolution']=f'{MODELS[model][0]} degree' if model=='era5' else '9 km'
                path.parent.mkdir(parents=True,exist_ok=True); frame.to_parquet(path,index=False); break
        print(f'chunk {i}/{len(rows)} {slug} ({lat:.4f},{lon:.4f}) {a}..{b} weight={weight(a,b)} cached={path.exists() and valid_chunk(path)} returned_cells={len(cell_owner[slug])}',flush=True)

if __name__=='__main__': main()

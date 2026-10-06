#!/usr/bin/env python3
"""Quota-bounded, resumable downloads for TASK 6 rain-source comparisons."""
from __future__ import annotations
from datetime import date
from pathlib import Path
import argparse,gzip,json,math,time
import numpy as np
import pandas as pd
import requests
from floodrisk.cities import CITIES

TURN_STATE=Path('data/raw/open_meteo/.task6_weight.json')
TURN_CAP=3500
UA='floodrisk-hackathon/0.1 (historical precipitation comparison; contact unavailable)'
SOURCES={
 'historical_forecast':{'url':'https://historical-forecast-api.open-meteo.com/v1/forecast','years':[2022,2023,2024],'models':None},
 'ecmwf_ifs':{'url':'https://archive-api.open-meteo.com/v1/archive','years':[2017,2018,2022,2023,2024],'models':'ecmwf_ifs'},
}

def points(city):
    w,s,e,n=CITIES[city].bbox
    ny,nx=(3,3) if city=='ho_chi_minh' else (2,3)
    return [(float(y),float(x)) for y in np.linspace(s,n,ny) for x in np.linspace(w,e,nx)]
def weight(nloc,start,end):return nloc*math.ceil(((end-start).days+1)/14)
def reserve(w):
    try:state=json.loads(TURN_STATE.read_text())
    except (OSError,ValueError):state={'weight_used':0}
    if state.get('weight_used',0)+w>TURN_CAP:raise RuntimeError(f"TASK6 Open-Meteo turn cap {TURN_CAP} would be exceeded ({state.get('weight_used',0)}+{w})")
    # Reuse the ERA5 downloader's persisted hourly/daily quota counters.
    from download_rain import wait_for_budget
    wait_for_budget(w)
    state['weight_used']=state.get('weight_used',0)+w;state['cap']=TURN_CAP;state['last_reserved']=w
    TURN_STATE.parent.mkdir(parents=True,exist_ok=True);tmp=TURN_STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(TURN_STATE)
    return state['weight_used']
def fetch_one(source,city,year,session):
    cfg=SOURCES[source];locs=points(city);a=date(year,1,1);b=date(year,12,31)
    stem=Path('data/raw/rain_source_experiments')/source/city/f'{year}'
    pq=stem.with_suffix('.parquet');raw=stem.with_suffix('.json.gz');meta=stem.with_suffix('.meta.json')
    if pq.exists() and raw.exists() and meta.exists():return {'cached':True,'weight':0,'rows':len(pd.read_parquet(pq,columns=['time']))}
    w=weight(len(locs),a,b);total=reserve(w)
    params={'latitude':','.join(f'{lat:.6f}' for lat,lon in locs),'longitude':','.join(f'{lon:.6f}' for lat,lon in locs),'start_date':a.isoformat(),'end_date':b.isoformat(),'hourly':'precipitation','timezone':'Asia/Ho_Chi_Minh'}
    if cfg['models']:params['models']=cfg['models']
    time.sleep(1.1)
    response=session.get(cfg['url'],params=params,timeout=180)
    if response.status_code==429:
        raise RuntimeError(f"HTTP 429 (STOP, no retry) for {response.url}: {response.text[:1200]}")
    try:response.raise_for_status()
    except requests.RequestException as exc:raise RuntimeError(f"HTTP {response.status_code} at {response.url}: {response.text[:1200]}") from exc
    payload=response.json();items=payload if isinstance(payload,list) else [payload]
    rows=[];resolved=[]
    for i,obj in enumerate(items):
        hourly=obj.get('hourly') or {};times=hourly.get('time',[]);prec=hourly.get('precipitation',[])
        if not times or len(times)!=len(prec):raise RuntimeError(f"Invalid/non-null precipitation response at {response.url}; item {i}")
        rlat=float(obj.get('latitude',locs[min(i,len(locs)-1)][0]));rlon=float(obj.get('longitude',locs[min(i,len(locs)-1)][1]))
        resolution=obj.get('grid_resolution') or obj.get('resolution') or obj.get('model')
        resolved.append({'latitude_returned':rlat,'longitude_returned':rlon,'elevation':obj.get('elevation'),'model_field':obj.get('model'),'generationtime_ms':obj.get('generationtime_ms'),'hourly_units':obj.get('hourly_units')})
        frame=pd.DataFrame({'time':pd.to_datetime(times),'precipitation':pd.to_numeric(prec,errors='coerce'),'latitude_returned':rlat,'longitude_returned':rlon,'requested_latitude':locs[min(i,len(locs)-1)][0],'requested_longitude':locs[min(i,len(locs)-1)][1],'model':source,'model_parameter':cfg['models'] or 'best_match (endpoint default)'})
        rows.append(frame)
    if len(items)!=len(locs):raise RuntimeError(f"Expected {len(locs)} locations, API returned {len(items)} objects at {response.url}")
    result=pd.concat(rows,ignore_index=True)
    if result.precipitation.isna().all():raise RuntimeError(f"All precipitation values null at {response.url}")
    stem.parent.mkdir(parents=True,exist_ok=True)
    result.to_parquet(pq,index=False)
    with gzip.open(raw,'wt',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'))
    info={'source':source,'city':city,'year':year,'url':response.url,'http_status':response.status_code,'requested_locations':locs,'returned_locations':resolved,'hourly_rows':len(result),'weighted_cost':w,'cumulative_turn_weight':total,'response_keys':list(payload[0].keys()) if isinstance(payload,list) else list(payload.keys()),'model_parameter':cfg['models'] or 'Best Match (endpoint default)','license':'Open-Meteo attribution-required CC BY 4.0; verify provider model terms for redistribution'}
    meta.write_text(json.dumps(info,indent=2));return {'cached':False,'weight':w,'rows':len(result),'models':resolved}

def download(pilot=False):
    session=requests.Session();session.headers.update({'User-Agent':UA,'Accept':'application/json'})
    plan=[]
    for source,cfg in SOURCES.items():
        for city in ('ho_chi_minh','da_nang'):
            for year in cfg['years']:plan.append((source,city,year))
    if pilot: plan=plan[:1]
    for i,(source,city,year) in enumerate(plan,1):
        print(f'[{i}/{len(plan)}] {source} {city} {year}',flush=True)
        result=fetch_one(source,city,year,session)
        print(json.dumps({'source':source,'city':city,'year':year,**result},default=str),flush=True)
    print('turn weight state:',TURN_STATE.read_text(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');p.add_argument('--pilot',action='store_true');a=p.parse_args()
    if a.pilot:download(pilot=True)
    elif a.download:download()

#!/usr/bin/env python3
"""Fetch Open-Meteo ERA5 precipitation on its native quarter-degree grid.

Each batch requests 2002-01-01 through yesterday once and writes one Parquet per
point. Returned grid coordinates are retained to document actual grid snapping.
"""
from datetime import date, timedelta
from pathlib import Path
import json, math, time
import pandas as pd
import requests
from floodrisk.cities import CITIES

BASE=Path('data/raw/open_meteo')
API='https://archive-api.open-meteo.com/v1/archive'
VARS=['precipitation','rain']
MODEL='era5'
GRID=0.25
BATCH_SIZE=8

def points_for_bbox(b):
    w,s,e,n=b
    # ERA5 native grid is 0.25 degrees; request only grid nodes inside bbox.
    def axis(lo,hi):
        first=math.ceil(lo/GRID-1e-10)*GRID
        vals=[]; v=first
        while v<=hi+1e-9:
            vals.append(round(v,3)); v+=GRID
        return vals
    return [(lat,lon) for lat in axis(s,n) for lon in axis(w,e)]

def valid_cache(path):
    if not path.exists(): return False
    try:
        df=pd.read_parquet(path,columns=['precipitation','model'])
        return not df.empty and df['precipitation'].notna().any() and (df['model']=='ERA5').all()
    except Exception: return False

def main():
    end=date.today()-timedelta(days=1)
    session=requests.Session()
    for slug,city in CITIES.items():
        points=points_for_bbox(city.bbox)
        print(f'{slug}: {len(points)} grid points; ERA5 nominal 0.25 degree; requested 2002-01-01..{end}',flush=True)
        missing=[]
        for lat,lon in points:
            path=BASE/slug/f'{lat:.2f}_{lon:.2f}.parquet'
            if not valid_cache(path): missing.append((lat,lon,path))
        for i in range(0,len(missing),BATCH_SIZE):
            batch=missing[i:i+BATCH_SIZE]
            params={'latitude':','.join(str(x[0]) for x in batch),
                    'longitude':','.join(str(x[1]) for x in batch),
                    'start_date':'2002-01-01','end_date':end.isoformat(),
                    'hourly':','.join(VARS),'timezone':'Asia/Ho_Chi_Minh','models':MODEL}
            response=None
            for attempt in range(7):
                response=session.get(API,params=params,timeout=240)
                if response.status_code == 429 and 'Hourly API request limit exceeded' in response.text:
                    print(f'Open-Meteo hourly quota exhausted: {response.text[:500]}',flush=True)
                    raise RuntimeError(f'Open-Meteo hourly request quota reset required; cached Parquets retained: {response.url}')
                if response.status_code == 429 or response.status_code in (502,503,504):
                    delay=61 if response.status_code == 429 else min(60,10*(attempt+1)); print(f'Open-Meteo HTTP {response.status_code}: {response.text[:500]}; backing off {delay}s',flush=True); time.sleep(delay); continue
                break
            response.raise_for_status()
            records=response.json()
            if isinstance(records,dict): records=[records]
            if len(records)!=len(batch): raise RuntimeError(f'API returned {len(records)} locations for batch of {len(batch)}')
            for ((lat,lon,path),record) in zip(batch,records):
                hourly=record.get('hourly',{})
                frame=pd.DataFrame(hourly)
                if frame.empty: raise RuntimeError(f'Empty hourly response for {lat},{lon}')
                frame.insert(0,'time',pd.to_datetime(frame.pop('time')))
                frame['latitude_returned']=record.get('latitude')
                frame['longitude_returned']=record.get('longitude')
                frame['elevation_returned_m']=record.get('elevation')
                frame['requested_latitude']=lat; frame['requested_longitude']=lon
                frame['model']='ERA5'; frame['nominal_grid_resolution']='0.25 degree'
                path.parent.mkdir(parents=True,exist_ok=True)
                frame.to_parquet(path,index=False)
                print(f'{path}: rows={len(frame)} snapped={record.get("latitude")},{record.get("longitude")}',flush=True)
            time.sleep(61)
        # Empirical coordinates confirm the actual returned model grid step.
        returned=[]
        for lat,lon in points:
            p=BASE/slug/f'{lat:.2f}_{lon:.2f}.parquet'
            if p.exists():
                df=pd.read_parquet(p,columns=['latitude_returned','longitude_returned'])
                returned.append((float(df.latitude_returned.iloc[0]),float(df.longitude_returned.iloc[0])))
        lats=sorted({x[0] for x in returned}); lons=sorted({x[1] for x in returned})
        print(f'{slug}: returned grid latitude steps={sorted({round(b-a,5) for a,b in zip(lats,lats[1:])})}; longitude steps={sorted({round(b-a,5) for a,b in zip(lons,lons[1:])})}',flush=True)

if __name__=='__main__': main()

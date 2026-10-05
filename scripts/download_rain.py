#!/usr/bin/env python3
"""Download Open-Meteo ERA5-Land hourly precipitation on its ~0.1 degree grid.
Results are cached by requested point/year as Parquet; point batches exploit the API's multi-location response.
"""
from datetime import date, timedelta
from pathlib import Path
import json, math, time
import pandas as pd
import requests
from floodrisk.cities import CITIES

BASE=Path('data/raw/open_meteo')
API='https://archive-api.open-meteo.com/v1/archive'
VARS=['precipitation','rain','showers']

def get_bboxes():
    p=Path('data/raw/osm/city_bboxes.json')
    if not p.exists(): raise SystemExit('Run scripts/fetch_city_bboxes.py first')
    return json.loads(p.read_text())

def points_for_bbox(b):
    w,s,e,n=b
    # ERA5-Land nominal grid is ~0.1 degrees; snap regular points to tenth degrees.
    xs=[round(x,1) for x in [w+0.05+i*0.1 for i in range(max(1,math.ceil((e-w-0.05)/0.1)))]]
    ys=[round(y,1) for y in [s+0.05+i*0.1 for i in range(max(1,math.ceil((n-s-0.05)/0.1)))]]
    return sorted({(x,y) for x in xs for y in ys if w<=x<=e and s<=y<=n})

def main():
    end=date.today()-timedelta(days=1)
    bboxes=get_bboxes(); sess=requests.Session()
    for slug in CITIES:
        pts=points_for_bbox(bboxes[slug]['bbox']); print(slug,len(pts),'points; nominal grid 0.1 degree (ERA5-Land)')
        for year in range(2002,end.year+1):
            st=f'{year}-01-01'; en=f'{year}-12-31' if year<end.year else end.isoformat()
            missing=[]
            for lat,lon in pts:
                p=BASE/slug/f'{lat:.1f}_{lon:.1f}'/f'{year}.parquet'
                if not p.exists(): missing.append((lat,lon,p))
            for i in range(0,len(missing),50):
                batch=missing[i:i+50]
                params={'latitude':','.join(str(x[0]) for x in batch),'longitude':','.join(str(x[1]) for x in batch),'start_date':st,'end_date':en,'hourly':','.join(VARS),'timezone':'Asia/Ho_Chi_Minh','models':'era5_land'}
                r=sess.get(API,params=params,timeout=180); r.raise_for_status(); records=r.json()
                if isinstance(records,dict): records=[records]
                for (lat,lon,path),record in zip(batch,records):
                    h=record.get('hourly',{}); df=pd.DataFrame(h)
                    if not df.empty:
                        df.insert(0,'time',pd.to_datetime(df.pop('time')))
                        df['latitude_returned']=record.get('latitude'); df['longitude_returned']=record.get('longitude')
                        df['elevation_returned_m']=record.get('elevation'); df['model']='era5_land'
                    path.parent.mkdir(parents=True,exist_ok=True); df.to_parquet(path,index=False)
                time.sleep(1.05)
            print(slug,year,'cached',len(pts),'points')
if __name__=='__main__': main()

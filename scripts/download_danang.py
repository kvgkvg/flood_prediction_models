#!/usr/bin/env python3
"""Cache Da Nang portal resources and normalize its public flood reports.

Only endpoint paths and query behavior visible in the downloaded public page
bundle are used. Existing JSON is reused on reruns.
"""
from pathlib import Path
import json, time
import pandas as pd
import requests

ROOT=Path('data/raw/danang_portal')
BASE='https://muangap-api.danang.gov.vn'
HEADERS={'User-Agent':'floodrisk-hackathon/0.1 (contact: team email unknown)','Accept':'application/json'}
ENDPOINTS={
 'reports':('/v1/flood/reports',None),
 'resources':('/v2/client/resource/list',{}),
 'resource_types':('/v2/client/resource_type/list',{}),
 'water_stations':('/v2/client/water_station/list_all',None),
}
def main():
 ROOT.mkdir(parents=True,exist_ok=True); s=requests.Session(); s.headers.update(HEADERS)
 for name,(path,params) in ENDPOINTS.items():
  dest=ROOT/f'{name}.json'
  if dest.exists(): print(f'cached {dest}'); continue
  r=s.get(BASE+path,params=params,timeout=90)
  if r.status_code==403 or 'blocked' in r.text.lower() or 'captcha' in r.text.lower():
   raise RuntimeError(f'Portal blocked endpoint {r.url}: HTTP {r.status_code}: {r.text[:2000]}')
  if r.status_code!=200: raise RuntimeError(f'Portal endpoint failed {r.url}: HTTP {r.status_code}: {r.text[:2000]}')
  dest.write_bytes(r.content); print(f'{dest}: HTTP {r.status_code}, {len(r.content)} bytes')
  time.sleep(2.1)
 data=json.loads((ROOT/'reports.json').read_text())['data']
 rows=[]
 for x in data:
  loc=x.get('location') or {}; coords=loc.get('coordinates') or [None,None]
  ft=x.get('flood_time') or {}; depth=x.get('water_level')
  if depth is not None and x.get('flood_unit')=='m': depth=float(depth)*100
  ts=ft.get('start_time')
  dt=pd.to_datetime(ts,unit='s',utc=True).tz_convert('Asia/Ho_Chi_Minh') if ts else pd.NaT
  rows.append({'id':x.get('_id'),'lat':coords[1] if len(coords)>1 else None,'lon':coords[0] if coords else None,
   'datetime':dt,'depth_cm':depth,'address_road_text':loc.get('address') or x.get('flood_location_details'),
   'status':x.get('floodStatus'),'flood_type':x.get('flood_type'),'flood_unit':x.get('flood_unit')})
 frame=pd.DataFrame(rows); frame.to_parquet(ROOT/'flood_reports.parquet',index=False)
 dates=frame['datetime'].dropna()
 hold=int((frame.datetime.dt.year>=2025).sum())
 print(f'reports={len(frame)} distinct_dates={dates.dt.date.nunique()} range={dates.min()}..{dates.max()} rows_2022-10-14={int((dates.dt.date==pd.Timestamp("2022-10-14").date()).sum())} holdout_2025_2026_count={hold}')
 if (ROOT/'water_stations.json').exists():
  station=json.loads((ROOT/'water_stations.json').read_text()); print(f'water_station_records={len(station) if isinstance(station,list) else len(station.get("data",[]))}')
if __name__=='__main__':main()

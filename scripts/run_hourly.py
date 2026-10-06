#!/usr/bin/env python3
"""Hourly route risk runner; live mode requests forecast, offline mode replays a pre-2025 event."""
from __future__ import annotations
import argparse,gzip,json,math
from datetime import timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from scipy.special import expit
from floodrisk.cities import CITIES
from floodrisk.combine import route_bands
from floodrisk.trigger import _apply

UA='floodrisk-hackathon/0.1 (hourly route-risk forecast; contact unavailable)'
TZ='Asia/Ho_Chi_Minh'
def grid(city):
    if city in CITIES:w,s,e,n=CITIES[city].bbox
    else:
        import geopandas as gpd
        b=gpd.read_parquet(Path('data/processed')/city/'routes.parquet',columns=['geometry']).total_bounds;w,s,e,n=map(float,b)
    ny,nx=(3,3) if city=='ho_chi_minh' else (2,3)
    return [(float(y),float(x)) for y in np.linspace(s,n,ny) for x in np.linspace(w,e,nx)]

def _offline(city):
    rec=pd.read_parquet('data/processed/flood_records.parquet',columns=['city','date','cause','split'],filters=[('split','in',['train','train_undated'])])
    rec=rec[(rec.city==city)&rec.date.notna()&rec.cause.isin(['rain','combined'])&(pd.to_datetime(rec.date)<pd.Timestamp('2025-01-01'))].sort_values('date',ascending=False)
    root=Path('data/raw/rain_source_experiments/ecmwf_ifs')/city
    if rec.empty:raise RuntimeError(f'{city}: no pre-2025 rain flood day available for offline sample')
    for day in pd.to_datetime(rec.date).dt.normalize():
        p=root/f'{day.year}.parquet'
        if p.exists():
            at=day.tz_localize(TZ)+pd.Timedelta(hours=12);return p,at
    raise FileNotFoundError(f'{city}: no IFS hourly cache for an unlocked flood day')

def _offline_weather(city,at):
    p,_=_offline(city)
    d=pd.read_parquet(p,columns=['time','precipitation','latitude_returned','longitude_returned'])
    d['time']=pd.to_datetime(d.time,errors='coerce');lo=at.tz_localize(None)-pd.Timedelta(hours=72);hi=at.tz_localize(None)+pd.Timedelta(hours=6)
    d=d[(d.time>=lo)&(d.time<=hi)]
    s=d.groupby('time').precipitation.max().sort_index().astype(float);s.index=s.index.tz_localize(TZ);return s

def _live_weather(city,at,model):
    pts=grid(city);url='https://api.open-meteo.com/v1/forecast'
    params={'latitude':','.join(f'{a:.6f}' for a,b in pts),'longitude':','.join(f'{b:.6f}' for a,b in pts),'hourly':'precipitation','past_hours':72,'forecast_hours':12,'timezone':TZ}
    if model!='best_match':params['models']=model
    session=requests.Session();session.headers.update({'User-Agent':UA,'Accept':'application/json'})
    r=session.get(url,params=params,timeout=90)
    if r.status_code==429:raise RuntimeError(f'forecast API returned HTTP 429 (no retry): {r.url}; {r.text[:500]}')
    if r.status_code in (400,422):raise ValueError(f'forecast model unavailable (HTTP {r.status_code}): {r.url}; {r.text[:500]}')
    try:r.raise_for_status()
    except requests.RequestException as e:raise RuntimeError(f'forecast API HTTP {r.status_code}: {r.url}; {r.text[:1000]}') from e
    payload=r.json();items=payload if isinstance(payload,list) else [payload]
    if len(items)!=len(pts):raise ValueError(f'forecast response had {len(items)} locations, expected {len(pts)}')
    frames=[]
    for item in items:
        h=item.get('hourly') or {};times=pd.to_datetime(h.get('time',[]));vals=pd.to_numeric(pd.Series(h.get('precipitation',[])),errors='coerce')
        if times.empty or vals.isna().all():raise ValueError(f'forecast API returned empty precipitation: {r.url}')
        if times.tz is None:times=times.tz_localize(TZ)
        frames.append(pd.Series(vals.to_numpy(),index=times))
    d=pd.concat(frames,axis=1).max(axis=1).sort_index();return d,r.url

def _quantile(value,ref):
    x=pd.to_numeric(ref,errors='coerce').dropna().to_numpy(float);return float(np.searchsorted(np.sort(x),value,side='right')/max(1,len(x)))

def _trigger_rain(values,city,model_dir,cdf_source='ifs'):
    cfg=json.loads((Path(model_dir)/'rain_trigger.json').read_text());ref=pd.read_parquet(Path(model_dir)/'cdfs'/f'{city}_{cdf_source}_reference.parquet')
    out=[]
    for v in values:
        q3=_quantile(v['rain_max_3h_mm'],ref.rain_max_3h_mm);qt=_quantile(v['rain_total_mm'],ref.rain_total_mm)
        q={'rain_max_3h_mm':np.clip(q3,.001,.999),'rain_total_mm':np.clip(qt,.001,.999)}
        z=np.asarray([math.log(q[c]/(1-q[c])) for c in cfg['selected_features']]);tr=float(expit(np.dot(z,np.asarray(cfg['coef']))+cfg['intercept']))
        v=dict(v);v['q_max3h']=q3;v['q_total']=qt;v['T_rain']=tr;out.append(v)
    return out

def _tide_at(city,times):
    if city!='ho_chi_minh':return [0.]*len(times)
    hourly=pd.read_parquet('data/processed/ho_chi_minh/drivers_tide_hourly.parquet',columns=['time_utc','astro_m']);hourly['time_utc']=pd.to_datetime(hourly.time_utc,utc=True);idx=hourly.set_index('time_utc').astro_m
    model=json.loads(Path('models/m2_ho_chi_minh_tide.json').read_text());return [float(_apply(model,pd.DataFrame({'astro_daily_max_m':[idx.loc[t.tz_convert('UTC')]]}))[0]) for t in times]

def run(city,at=None,offline_sample=False,model_dir='models/final_2025-01-01',rain_model='ecmwf_ifs',pilot=False):
    model=Path(model_dir)
    if not (Path('data/processed')/city/'routes.parquet').exists() or not (model/city/'route_susceptibility.parquet').exists():raise FileNotFoundError(f'{city}: route/model files missing')
    if offline_sample:
        p,chosen=_offline(city);at=chosen
        series=_offline_weather(city,at);weather_source=f'cached IFS replay: {p}';cdf_source='ifs';effective_model='cached IFS replay'
    else:
        at=pd.Timestamp.now(tz=TZ) if at is None else pd.Timestamp(at)
        if at.tzinfo is None:at=at.tz_localize(TZ)
        else:at=at.tz_convert(TZ)
        try:series,weather_source=_live_weather(city,at,rain_model);cdf_source='ifs' if rain_model=='ecmwf_ifs' else 'era5';effective_model=rain_model
        except ValueError as exc:
            if rain_model!='ecmwf_ifs' or 'forecast model unavailable' not in str(exc):raise
            # Only fall back for an unsupported model response; no retry on rate limits or access blocks.
            series,weather_source=_live_weather(city,at,'best_match');cdf_source='era5';effective_model='best_match fallback'
    at=pd.Timestamp(at)
    if at.tzinfo is None:at=at.tz_localize(TZ)
    else:at=at.tz_convert(TZ)
    at=at.floor('h')  # rain and tide series are hourly; an unaligned "now" breaks the tide lookup
    inputs=[]
    for h in range(3):
        t=at+pd.Timedelta(hours=h);sub=series.loc[(series.index>t-pd.Timedelta(hours=6))&(series.index<=t)].dropna()
        if len(sub)<6:raise ValueError(f'insufficient trailing 6-hour rain window at {t}')
        total24=series.loc[(series.index>t-pd.Timedelta(hours=24))&(series.index<=t)].dropna().sum()
        inputs.append({'valid_time':t,'rain_max_3h_mm':float(sub.rolling(3,min_periods=3).sum().max()),'rain_total_mm':float(total24)})
    rain_rows=_trigger_rain(inputs,city,model,cdf_source);tide_ts=[x['valid_time'] for x in rain_rows];tides=_tide_at(city,tide_ts)
    sus=pd.read_parquet(model/city/'route_susceptibility.parquet');
    if pilot:sus=sus.head(500).copy()
    route_ids=sus.route_id.astype(str).to_numpy();sr=sus.S_hyb_rain.to_numpy(np.float32);st=sus.S_hyb_tide.to_numpy(np.float32);uni=sus.in_universe.to_numpy(bool)
    bands_r=route_bands(sr,sr,np.ones(len(sus),bool));bands_t=route_bands(st,st,np.ones(len(sus),bool))
    bandname=lambda a:np.where(a==2,'A',np.where(a==1,'B','C'))
    thresholds=json.loads(Path('models/combination_thresholds.json').read_text())['thresholds'][city];config=json.loads(Path('models/final_config.json').read_text());thresholds['rain']={'t_lo':config['q_watch'],'t_hi':config['q_alert']}
    hist=sus.H_any.fillna(0).to_numpy(bool);depth=np.full(len(sus),np.nan)
    records=pd.read_parquet('data/processed/flood_records.parquet',columns=['record_id','city','date','depth_cm','split'],filters=[('split','in',['train','train_undated'])]);records=records[(records.city==city)&(records.date.isna()|(pd.to_datetime(records.date)<pd.Timestamp('2025-01-01')))]
    match=pd.read_parquet('data/processed/flood_record_matches.parquet',columns=['record_id','route_id']);z=records.merge(match,on='record_id').dropna(subset=['route_id']);dm=z.groupby('route_id').depth_cm.max().to_dict();depth=np.asarray([dm.get(r,np.nan) for r in route_ids],float)
    rows=[]
    for i,tdata in enumerate(rain_rows):
        tt=tides[i];tr=tdata['T_rain'];pl=1-(1-sr*tr)*(1-st*tt)
        rainstate=0 if tr<thresholds['rain']['t_lo'] else 1 if tr<thresholds['rain']['t_hi'] else 2;tstate=0 if tt<thresholds['tide']['t_lo'] else 1 if tt<thresholds['tide']['t_hi'] else 2
        lr=np.where(rainstate==2,np.where(bands_r==2,2,np.where(bands_r==1,1,0)),np.where((rainstate==1)&(bands_r==2),1,0))
        lt=np.where(tstate==2,np.where(bands_t==2,2,np.where(bands_t==1,1,0)),np.where((tstate==1)&(bands_t==2),1,0));level=np.maximum(lr,lt)
        rows.extend({'route_id':route_ids[j],'valid_time':tdata['valid_time'],'horizon_h':i,'P':float(pl[j]),'level':('low','medium','high')[int(level[j])],'S_rain':float(sr[j]),'S_tide':float(st[j]),'T_rain':tr,'T_tide':tt,'day_state_rain':('quiet','watch','alert')[rainstate],'day_state_tide':('quiet','watch','alert')[tstate],'provenance':'official_observation' if hist[j] else 'model_forecast','active_report_count':0,'max_recorded_depth_cm':None if not np.isfinite(depth[j]) else float(depth[j])} for j in range(len(sus)))
    frame=pd.DataFrame(rows)
    if pilot:print(f'pilot {city}: {len(frame)} risk rows; schema={frame.columns.tolist()}; sample={offline_sample}');return frame
    out=Path('data/export')/city;out.mkdir(parents=True,exist_ok=True);frame.to_parquet(out/'risk_hourly.parquet',index=False,compression='zstd')
    with gzip.open(out/'risk_hourly.json.gz','wt',encoding='utf-8') as f:json.dump(frame.to_dict('records'),f,separators=(',',':'),default=str)
    verified=False
    if Path('reports/locked_results.tsv').exists():
        locked=pd.read_csv('reports/locked_results.tsv',sep='\t');q=locked[(locked.city==city)&(locked.metric=='D1')]
        verified=bool(len(q) and q.n_records.max()>0 and q.n_flood_days.max()>0)
    status={'city':city,'confidence':'verified' if verified else 'estimated_unverified','model_version':'final_2025-01-01','rain_source':f'{effective_model}; {cdf_source.upper()} CDF','generated_at':pd.Timestamp.now(tz=TZ).isoformat(),'offline_sample':bool(offline_sample),'sample_at':at.isoformat() if offline_sample else None,'weather_source':weather_source,'locked_evaluation_attached':bool(verified)}
    (out/'city_status.json').write_text(json.dumps(status,indent=2));print(json.dumps({'city':city,'rows':len(frame),'offline_sample':offline_sample,'output':str(out),'parquet_bytes':(out/'risk_hourly.parquet').stat().st_size},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--city',required=True);p.add_argument('--at');p.add_argument('--offline-sample',action='store_true');p.add_argument('--model-dir',default='models/final_2025-01-01');p.add_argument('--rain-model',choices=['ecmwf_ifs','best_match'],default='ecmwf_ifs');p.add_argument('--pilot',action='store_true');a=p.parse_args();run(a.city,a.at,a.offline_sample,a.model_dir,a.rain_model,a.pilot)

#!/usr/bin/env python3
"""DEV evaluation of pooled percentile trigger with ERA5 and IFS inputs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

CONF=json.loads(Path('models/rain_percentile_trigger.json').read_text())
LO,HI=CONF['states']['q_watch'],CONF['states']['q_alert']
BOOT=1000
def ci_auc(y,s,seed=331,n=None):
    n=BOOT if n is None else n
    y=np.asarray(y,int);s=np.asarray(s,float);p=np.flatnonzero(y);q=np.flatnonzero(~y.astype(bool))
    if not len(p) or not len(q):return np.nan,(np.nan,np.nan)
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(n):
        ix=np.r_[rng.choice(p,len(p),True),rng.choice(q,len(q),True)];vals.append(roc_auc_score(y[ix],s[ix]))
    return float(roc_auc_score(y,s)),tuple(map(float,np.quantile(vals,[.025,.975])))
def ci_prop(x,seed=332,n=None):
    n=BOOT if n is None else n
    x=np.asarray(x,float);rng=np.random.default_rng(seed);b=[np.mean(x[rng.integers(0,len(x),len(x))]) for _ in range(n)]
    return float(np.mean(x)),tuple(map(float,np.quantile(b,[.025,.975])))
def fmt(z):return f'{z[0]:.3f} [{z[1][0]:.3f}, {z[1][1]:.3f}]'
def main(pilot=False):
    global BOOT
    if pilot:BOOT=100
    lab=pd.read_parquet('data/processed/flood_records.parquet',columns=['city','date','cause','split'],filters=[('split','in',['train','train_undated'])]);lab['date']=pd.to_datetime(lab.date,errors='coerce').dt.normalize();lab=lab[lab.date.notna()]
    rows=[]
    for city in ('ho_chi_minh','da_nang'):
        rain_dates=set(lab.loc[(lab.city==city)&lab.cause.isin(['rain','combined']),'date'])
        all_dates=set(lab.loc[lab.city==city,'date'])
        for source in ('era5','ifs'):
            d=pd.read_parquet(Path('data/processed/rain_percentiles')/f'{city}_{source}.parquet');d.date=pd.to_datetime(d.date).dt.normalize();d=d.set_index('date')
            d=d.loc[(d.index>='2023-01-01')&(d.index<'2025-01-01')].dropna(subset=['T_rain']);y=np.array([day in rain_dates for day in d.index],int);t=d.T_rain.to_numpy(float)
            watch=(t>=LO)&(t<HI);alert=t>=HI;wa=t>=LO
            flood=y==1;seas=np.array([(5<=x.month<=11) if city=='ho_chi_minh' else (9<=x.month<=12) for x in d.index]);noreport=seas & np.array([day not in all_dates for day in d.index]);dry=~seas
            rows.append({'city':city,'source':source,'n_days':len(d),'flood_days':int(flood.sum()),'auc':ci_auc(y,t,400+len(rows)),'flood_watch':ci_prop(watch[flood]),'flood_alert':ci_prop(alert[flood]),'flood_watch_alert':ci_prop(wa[flood]),'rain_no_report_watch_alert':ci_prop(wa[noreport]),'rain_no_report_alert':ci_prop(alert[noreport]),'dry_watch_alert':ci_prop(wa[dry]),'dry_alert':ci_prop(alert[dry]),'thresholds':[LO,HI]})
    text=['# Shared percentile rain trigger — DEV results','',f"Selected FIT-only form: {', '.join(CONF['selected_features'])}; clipped logit transforms of source/city-specific daily climatological percentiles. Model pooled HCMC + Da Nang FIT days using ERA5 percentiles. LOYO selection CV mean AUC by candidate: "+'; '.join(f"{v['features']}={v['mean_auc']:.3f} over {len(v['folds'])} estimable years" for v in CONF['candidate_cv'].values())+'.',f"Shared thresholds: q_watch={LO:.6f}, q_alert={HI:.6f}. Watch covers {CONF['states']['watch_or_alert_sensitivity']:.1%} of FIT positives; alert covers {CONF['states']['alert_sensitivity']:.1%} while {CONF['states']['no_report_quiet']:.1%} of pooled rainy-season no-report days remain quiet. Thus 85% watch is met; alert >=60% with <=10% false alerts is not. The full FIT trade-off curve is stored in `models/rain_percentile_trigger.json`.",'','All AUC intervals use 1,000 stratified day bootstrap draws. Watch/alert shares use 1,000 day bootstrap draws. DEV labels are only 2023–2024 dated `train`/`train_undated` records; locked records are not loaded. Quiet state means T < q_watch, watch is q_watch <= T < q_alert, alert is T >= q_alert. Rainy seasons: HCMC May–Nov; Da Nang Sep–Dec. Unreported days are not confirmed dry.','', '| City | Rain input | DEV flood days / days | AUC | Flood days in watch | Flood days in alert | Flood days watch/alert | Rainy no-report days watch/alert | Dry-season days watch/alert |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:text.append(f"| {r['city']} | {r['source']} | {r['flood_days']} / {r['n_days']} | {fmt(r['auc'])} | {fmt(r['flood_watch'])} | {fmt(r['flood_alert'])} | {fmt(r['flood_watch_alert'])} | {fmt(r['rain_no_report_watch_alert'])} | {fmt(r['dry_watch_alert'])} |")
    if not pilot:Path('reports/percentile_trigger_dev.md').write_text('\n'.join(text)+'\n')
    print('\n'.join(text))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');main(p.parse_args().pilot)

#!/usr/bin/env python3
"""Refit astronomical tide constants on 2020–2024 only; predict without labels."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from floodrisk.drivers import build_tide_drivers
from floodrisk.trigger import _apply

def run(pilot=False):
    hourly,daily,coef=build_tide_drivers(start='2025-01-01' if pilot else '2002-01-01',
        end='2025-12-31' if pilot else '2026-12-31',fit_start='2020-01-01',fit_end='2025-01-01',write=not pilot)
    tide=Path('data/raw/uhslc_vung_tau/uhslc_vung_tau_hourly.csv')
    raw=pd.read_csv(tide,skiprows=[1],usecols=['time','sea_level']);raw['time']=pd.to_datetime(raw.time,utc=True,errors='coerce');raw['sea_level']=pd.to_numeric(raw.sea_level,errors='coerce')
    fit_n=int(raw.time.between(pd.Timestamp('2020-01-01',tz='UTC'),pd.Timestamp('2024-12-31 23:59:59',tz='UTC')).mul(raw.sea_level.notna()).sum())
    if pilot:
        print(json.dumps({'pilot':True,'prediction_rows':len(hourly),'days':len(daily),'fit_observation_count':fit_n,'fit_window':'2020-01-01..2024-12-31','peak-date':str(daily.index.max().date()) if isinstance(daily.index,pd.DatetimeIndex) else str(daily.date.max())},default=str));return
    model=json.loads(Path('models/m2_ho_chi_minh_tide.json').read_text());daily['T_tide']=_apply(model,daily[['astro_daily_max_m']])
    driver=Path('data/processed/ho_chi_minh/trigger_daily.parquet');old=pd.read_parquet(driver)
    old['date']=pd.to_datetime(old.date).dt.normalize();new=daily[['date','T_tide']].copy();new['date']=pd.to_datetime(new.date).dt.normalize()
    old=old.drop(columns=['T_tide'],errors='ignore').merge(new,on='date',how='outer').sort_values('date')
    old.to_parquet(driver,index=False)
    meta={'fit_start':'2020-01-01','fit_end_exclusive':'2025-01-01','max_fit_observation_date':'2024-12-31','fit_observations':fit_n,'predicted_start':'2002-01-01','predicted_end':'2026-12-31','locked_labels_read':False,'trigger_form':'unchanged saved percentile trigger from models/m2_ho_chi_minh_tide.json'}
    out=Path('models/final_2025-01-01');out.mkdir(parents=True,exist_ok=True);(out/'tide_harmonic_metadata.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({'written':True,**meta},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');run(p.parse_args().pilot)

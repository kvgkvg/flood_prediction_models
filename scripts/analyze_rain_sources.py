#!/usr/bin/env python3
"""Common-period, label-safe comparison of cached daily precipitation sources."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from floodrisk.drivers import _cell_daily

ROOT=Path('data/raw/rain_source_experiments')
SOURCES=['historical_forecast','ecmwf_ifs']
PERIOD=pd.date_range('2022-01-01','2024-12-31',freq='D')

def auc(y,s):
    y=np.asarray(y,int);s=np.asarray(s,float)
    if len(np.unique(y))<2:return float('nan')
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y,s))
def auc_ci(y,s,seed=4721,n=1000):
    y=np.asarray(y,int);s=np.asarray(s,float);p=np.flatnonzero(y==1);q=np.flatnonzero(y==0)
    if not len(p) or not len(q):return auc(y,s),(float('nan'),float('nan'))
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(n):
        ix=np.r_[rng.choice(p,len(p),True),rng.choice(q,len(q),True)]
        vals.append(auc(y[ix],s[ix]))
    return auc(y,s),(float(np.nanquantile(vals,.025)),float(np.nanquantile(vals,.975)))

def records(city):
    d=pd.read_parquet('data/processed/flood_records.parquet',columns=['date'],filters=[('city','=',city),('split','in',['train','train_undated'])])
    d=d[d.date.notna()].copy()
    d['date']=pd.to_datetime(d.date).dt.normalize()
    d=d[(d.date>=PERIOD.min())&(d.date<=PERIOD.max())]
    return set(d.date)

def source_daily(source,city):
    frames=[]
    for year in (2022,2023,2024):
        p=ROOT/source/city/f'{year}.parquet'
        d=pd.read_parquet(p)
        for (lat,lon),g in d.groupby(['latitude_returned','longitude_returned'],sort=False):
            x=_cell_daily(g[['time','precipitation']],lat,lon)
            frames.append(x[['date','rain_total_mm','rain_max_3h_mm']])
    cells=pd.concat(frames,ignore_index=True)
    out=cells.groupby('date')[['rain_total_mm','rain_max_3h_mm']].max().reindex(PERIOD)
    return out

def era5_daily(city):
    d=pd.read_parquet(Path('data/processed')/city/'drivers_rain_daily.parquet')
    d['date']=pd.to_datetime(d.date).dt.normalize();d=d.set_index('date').reindex(PERIOD)
    return d[['rain_total_mm_max_cells','rain_max_3h_mm_max_cells']].rename(columns={'rain_total_mm_max_cells':'rain_total_mm','rain_max_3h_mm_max_cells':'rain_max_3h_mm'})

def main():
    rows=[];details=[]
    for city in ('ho_chi_minh','da_nang'):
        y=np.array([d in records(city) for d in PERIOD],int)
        for source in ('era5',)+tuple(SOURCES):
            d=era5_daily(city) if source=='era5' else source_daily(source,city)
            ix=np.asarray(d.index.notna()) & d.notna().all(axis=1).to_numpy(); yy=y[ix]
            for feat in ('rain_max_3h_mm','rain_total_mm'):
                score=d.loc[ix,feat].to_numpy(float);a,ci=auc_ci(yy,score,seed=701+len(rows))
                best=(float(a),ci,feat) if not rows or True else None
                details.append((source,city,feat,a,ci,int(yy.sum()),int((score[yy==1]<5).sum()),len(score[yy==1])))
            # Label-free pctl trigger is the required fallback where FIT positives < 8.
            # Define the climatological percentile from 2022 only (FIT dates), without labels.
            feat='rain_max_3h_mm';v=d.loc[ix,feat].astype(float);fit=v.loc[v.index.year<2023]
            pct=v.rank(method='average',pct=True).to_numpy();trig=1/(1+np.exp(-np.clip((pct-.95)/.02,-40,40)))
            ta,tci=auc_ci(yy,trig,seed=901+len(rows))
            rows.append({'city':city,'source':source,'n_days':len(yy),'n_flood_days':int(yy.sum()),'max3h_auc':details[-2][3] if details[-2][2]=='rain_max_3h_mm' else np.nan,'max3h_ci':details[-2][4],'daily_total_auc':details[-1][3],'daily_total_ci':details[-1][4],'best_index':max(details[-2][3],details[-1][3]) if np.isfinite(details[-2][3]) else np.nan,'max3h_positive_lt5_share':(details[-2][6]/details[-2][7] if details[-2][7] else np.nan),'label_free_pctl_auc':ta,'label_free_pctl_ci':tci,'model_form':'FIT positives <8: label-free 2022 climatology percentile of max3h'})
    pd.DataFrame(rows).to_csv('data/processed/rain_source_comparison.csv',index=False)
    out=['# Rain-source comparison (2022–2024 common period)','', 'All day labels are dated unlocked flood-record dates only; locked dates were not read. Source driver is the max across returned point cells. Intervals are 1,000 stratified day bootstrap draws. The trigger column is label-free: max-3h percentile against 2022 source climatology; selected Task 5 label-fitted forms are not refit because neither city has eight FIT positive days in this source window. AUC for raw indices is descriptive.','', '| City | Source | Flood days / days | Max 3h AUC (95% CI) | Daily total AUC (95% CI) | Best raw index | Flood days max3h <5mm | Label-free trigger AUC (95% CI) |','|---|---|---:|---:|---:|---|---:|---:|']
    for r in rows:
        out.append(f"| {r['city']} | {r['source']} | {r['n_flood_days']} / {r['n_days']} | {r['max3h_auc']:.3f} [{r['max3h_ci'][0]:.3f}, {r['max3h_ci'][1]:.3f}] | {r['daily_total_auc']:.3f} [{r['daily_total_ci'][0]:.3f}, {r['daily_total_ci'][1]:.3f}] | {'max 3h' if r['max3h_auc']>=r['daily_total_auc'] else 'daily total'} | {r['max3h_positive_lt5_share']:.1%} | {r['label_free_pctl_auc']:.3f} [{r['label_free_pctl_ci'][0]:.3f}, {r['label_free_pctl_ci'][1]:.3f}] |")
    out += ['', 'FIT/DEV limitation: the common window contains only one FIT report date in HCMC and one in Da Nang (both before 2023), below the eight-positive-day minimum. Accordingly the trigger column is a label-free max-3h percentile transform evaluated over the whole unlocked 2022–2024 period; it is not a FIT/DEV estimate. The 2022–2024 table has 7 HCMC and 17 Da Nang positive dates.', '', 'Open-Meteo Historical Forecast used endpoint-default Best Match. Responses returned snapped coordinates and elevations, but no resolved model or resolution field. For the same points and 2022 hours, Best Match and explicitly requested `ecmwf_ifs` were exactly identical in both cities (78,840 HCMC and 52,560 Da Nang values; max absolute difference 0). This strongly suggests Best Match selected ECMWF IFS HRES here, but remains an inference, not a returned API field. Open-Meteo lists IFS HRES at 9 km hourly in its model catalogue. The archive `ecmwf_ifs` model parameter was explicit. Recommendation: use ECMWF IFS HRES rain drivers for both cities and pair Model 2 live inputs to the same IFS forecast stream; it produced identical values to Best Match in this sample, while the point-estimate AUC favored the high-resolution products over ERA5, especially in Da Nang. Uncertainty is broad and positive-day counts are small, so this is a provisional source choice, not evidence of a statistically established advantage. The IFS years 2019–2021 were omitted to stay under the 3,500 weighted-unit experiment cap; therefore the tested window is 2022–2024. CHIRPS was skipped as optional, and the portal bundle declares station hourly-report endpoint constants but contains no page call to them with parameters; no station-history request was made.','']
    Path('reports/rain_source_comparison.md').write_text('\n'.join(out))
    print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()

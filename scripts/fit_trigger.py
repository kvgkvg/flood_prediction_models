#!/usr/bin/env python3
"""Fit Model 2 triggers on FIT and evaluate only the 2023–2024 DEV rehearsal."""
from pathlib import Path
import numpy as np
import pandas as pd
from floodrisk.trigger import (RAIN_SEASON,positive_dates,split_day_table,
    crossval_candidates,fit_selected,_apply,bootstrap_ci,reliability_table,save_json)

def _eligible_records():
    # Predicate pushdown keeps locked rows' attributes out of this process.
    return pd.read_parquet('data/processed/flood_records.parquet',columns=['city','date','cause','split'],filters=[('split','in',['train','train_undated'])])

def _count(rec,city,cause,start,end,months=None):
    cs={'rain':{'rain','combined'},'tide':{'tide','combined'}}[cause]
    x=rec[(rec.city==city)&rec.cause.isin(cs)&rec.date.notna()];d=pd.to_datetime(x.date,errors='coerce');ok=(d>=pd.Timestamp(start))&(d<pd.Timestamp(end));d=d[ok]
    if months is not None:d=d[d.dt.month.isin(months)]
    return int(d.dt.normalize().nunique())

def _add_residual_report(lines,tide_daily):
    z=tide_daily[(tide_daily.date>='2023-01-01')&(tide_daily.date<'2025-01-01')].dropna(subset=['observed_daily_max_m','astro_daily_max_m'])
    e=(z.astro_daily_max_m-z.observed_daily_max_m).to_numpy(float)
    if not len(e):lines+=['','DEV astronomical-vs-observed residual unavailable: no aligned observed dates.'];return
    rng=np.random.default_rng(54);boot=np.asarray([np.mean(e[rng.integers(0,len(e),len(e))]) for _ in range(1000)])
    lines+=['',f"DEV observed tide is diagnostic only (delivery delay; not an inference input): n={len(e)} days, signed mean residual {np.mean(e):.3f} m [bootstrap 95% CI {np.quantile(boot,.025):.3f},{np.quantile(boot,.975):.3f}], MAE {np.mean(np.abs(e)):.3f} m, RMSE {np.sqrt(np.mean(e**2)):.3f} m."]

def run():
    rec=_eligible_records()
    report=['# Model 2 trigger fit and DEV rehearsal','','FIT: dated observations before 2023-01-01. Undated `train_undated` observations cannot create day labels and are used only later in route susceptibility S. DEV: 2023-01-01 through 2024-12-31. All 2025+ records were predicate-filtered out before reading attributes.','', 'Negative controls are no-record days during HCMC May–November or Da Nang September–December. Dated positive days are retained in any month. Unreported days are treated as negatives, but many may be unreported flood days; this tends to depress apparent skill and miscalibrate probabilities.','', 'Rain comes from Open-Meteo ERA5 at 0.25° (~28 km here), city max/mean across cached cells. FIT-CV uses leave-one-year-out predictions. Candidate selection uses FIT-CV ROC AUC, AP tie-break; DEV is never used to select T. Intervals are day-stratified bootstrap intervals (500 FIT-CV / 1,000 DEV draws).','', '## Positive-day counts','','| City | Cause | FIT positive days (in season / all) | DEV positive days (in season / all) | Identification |','|---|---|---:|---:|---|']
    count_rows=[];section_start=len(report)
    for city in ('ho_chi_minh','da_nang'):
        rain=pd.read_parquet(f'data/processed/{city}/drivers_rain_daily.parquet');rain['date']=pd.to_datetime(rain.date).dt.normalize()
        tide_daily=None
        if city=='ho_chi_minh':
            tide_daily=pd.read_parquet('data/processed/ho_chi_minh/drivers_tide_daily.parquet');tide_daily['date']=pd.to_datetime(tide_daily.date).dt.normalize();daily=rain.merge(tide_daily,on='date',how='left')
        else:daily=rain.copy();daily['astro_daily_max_m']=0.;daily['astro_max_3d_m']=0.
        daily=daily[(daily.date>='2002-01-01')&(daily.date<'2025-01-01')].copy()
        positives={cause:positive_dates(rec,city,cause) for cause in ('rain','tide')}
        out=daily[['date']].copy()
        for cause in ('rain','tide'):
            pos=positives[cause]
            fit_all=_count(rec,city,cause,'2002-01-01','2023-01-01');dev_all=_count(rec,city,cause,'2023-01-01','2025-01-01')
            fit_season=_count(rec,city,cause,'2002-01-01','2023-01-01',RAIN_SEASON[city]);dev_season=_count(rec,city,cause,'2023-01-01','2025-01-01',RAIN_SEASON[city]);weak=fit_all<8
            count_rows.append(f"| {city} | {cause} | {fit_season} / {fit_all} | {dev_season} / {dev_all} | {'weakly identified (<8 FIT positive days)' if weak else '≥8 FIT positive days'} |")
            if cause=='tide' and city=='da_nang':
                param={'kind':'zero','candidate':'no_tide_driver','city':city,'cause':cause,'fit_start':None,'fit_end':None,'max_training_date':None,'n_fit_days':0,'n_fit_positive_days':0}
                save_json(f'models/m2_{city}_{cause}.json',param);out['T_tide']=np.float32(0);out['fitcv_T_tide']=np.nan;out['dev_y_tide']=0;continue
            table=split_day_table(city,cause,daily,pos)
            table.attrs['city']=city
            cv,cvpred,cvm=crossval_candidates(table,cause);param,fit=fit_selected(table,cause,cvm);param['city']=city
            if pd.Timestamp(param['max_training_date'])>=pd.Timestamp('2023-01-01'):raise AssertionError('DEV date entered a fitted trigger artifact')
            save_json(f'models/m2_{city}_{cause}.json',param)
            name=param['candidate'];dev=table[(table.date>='2023-01-01')&(table.date<'2025-01-01')];p_dev=_apply(param,dev)
            # Inference probabilities cover every unlocked calendar day; CV/DEV label columns are metadata for reports only.
            out[f'T_{cause}']=_apply(param,daily)
            pred_map={pd.Timestamp(dt):float(p) for dt,p in zip(cv.date,cvpred[name]) if np.isfinite(p)}
            out[f'fitcv_T_{cause}']=out.date.map(pred_map).astype('float32')
            out[f'dev_y_{cause}']=0
            devmap=dict(zip(dev.date,dev.positive.astype(int)));mask=out.date.isin(devmap);out.loc[mask,f'dev_y_{cause}']=out.loc[mask,'date'].map(devmap).astype(int)
            good=np.isfinite(cvpred[name]);cvpt,cvci=bootstrap_ci(cv.positive.to_numpy(bool)[good],cvpred[name][good],500,seed=881+len(name))
            dvpt,dvci=bootstrap_ci(dev.positive.to_numpy(bool),p_dev,1000,seed=991+len(city))
            report+=['',f'## {city} {cause}','',f"Selected T: `{name}` by best FIT leave-one-year-out ROC AUC (AP tie-break). Fit artifact max date: {param['max_training_date']}; FIT sample {param['n_fit_days']} days, {param['n_fit_positive_days']} positive days; weakly identified={weak}.",f"FIT LOO-CV AUC {cvpt['auc']:.3f} [{cvci['auc'][0]:.3f},{cvci['auc'][1]:.3f}], AP {cvpt['ap']:.3f} [{cvci['ap'][0]:.3f},{cvci['ap'][1]:.3f}]. DEV AUC {dvpt['auc']:.3f} [{dvci['auc'][0]:.3f},{dvci['auc'][1]:.3f}], AP {dvpt['ap']:.3f} [{dvci['ap'][0]:.3f},{dvci['ap'][1]:.3f}].",'', 'DEV reliability:','', '| Bin | Days | Mean T | Observed flood-day rate |','|---:|---:|---:|---:|']
            report += [f"| {r['bin']} | {r['n']} | {r['mean_p']:.3f} | {r['observed_rate']:.3f} |" for r in reliability_table(dev.positive,p_dev)]
            report+=['','FIT-CV candidates:','','| Candidate | AUC | AP |','|---|---:|---:|']
            for nm,(pt,ci) in cvm.items():report.append(f"| {nm} | {pt['auc']:.3f} [{ci['auc'][0]:.3f},{ci['auc'][1]:.3f}] | {pt['ap']:.3f} [{ci['ap'][0]:.3f},{ci['ap'][1]:.3f}] |")
        out.to_parquet(f'data/processed/{city}/trigger_daily.parquet',index=False)
        if city=='ho_chi_minh':
            if tide_daily is not None:_add_residual_report(report,tide_daily)
            d=split_day_table(city,'rain',daily,positives['rain']);v=d.rain_max_3h_mm_max_cells.dropna();yp=d.loc[v.index,'positive'].to_numpy(bool);posv=v.to_numpy()[yp];negv=v.to_numpy()[~yp]
            rng=np.random.default_rng(77);boot=np.asarray([np.mean(rng.choice(posv,len(posv),True)<5) for _ in range(1000)]) if len(posv) else np.array([np.nan]);share=float(np.mean(posv<5)) if len(posv) else np.nan
            report+=['','## ERA5 visibility for HCMC rain flood days','','Unlocked FIT+DEV dates, positives in any month and rainy-season negative controls. 0.25° is approximately 28 km at these latitudes; city value is the maximum across available cells.','',f"- Positive max-3h mm: n={len(posv)}, p10/median/p90={np.quantile(posv,[.1,.5,.9]).round(2).tolist() if len(posv) else 'NA'}; negative n={len(negv)}, p10/median/p90={np.quantile(negv,[.1,.5,.9]).round(2).tolist() if len(negv) else 'NA'}.",f"- Share of positive days with <5 mm city max-3h: {share:.1%} [{np.nanquantile(boot,.025):.1%},{np.nanquantile(boot,.975):.1%}] bootstrap 95% CI."]
    report[section_start:section_start]=count_rows
    Path('reports/m2_trigger.md').write_text('\n'.join(report)+'\n');print('wrote reports/m2_trigger.md; trigger_daily.parquet and M2 model JSONs for unlocked dates')

if __name__=='__main__':run()

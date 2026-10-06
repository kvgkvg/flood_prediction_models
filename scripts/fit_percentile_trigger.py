#!/usr/bin/env python3
"""Build label-free rain-driver CDFs and fit the pooled FIT-only trigger."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from floodrisk.drivers import _cell_daily

CITIES=('ho_chi_minh','da_nang')
OUT=Path('data/processed/rain_percentiles')
FIELDS=['rain_max_3h_mm','rain_total_mm','rain_prev_72h_mm']
SEASONS={'ho_chi_minh':set(range(5,12)),'da_nang':{9,10,11,12}}

def daily_ifs(city, pilot=False, years=None):
    root=Path('data/raw/rain_source_experiments/ecmwf_ifs')/city
    years=([2019] if pilot else list(range(2017,2025))) if years is None else list(years)
    chunks=[]
    for year in years:
        d=pd.read_parquet(root/f'{year}.parquet',columns=['time','precipitation','latitude_returned','longitude_returned'])
        chunks.append(d)
    raw=pd.concat(chunks,ignore_index=True).sort_values('time')
    parts=[]
    # Aggregate continuous cell time series so antecedent windows cross Jan 1 correctly.
    for (lat,lon),g in raw.groupby(['latitude_returned','longitude_returned'],sort=False):
        x=_cell_daily(g[['time','precipitation']],lat,lon)
        parts.append(x[['date','rain_max_3h_mm','rain_total_mm','rain_prev_72h_mm']])
    x=pd.concat(parts,ignore_index=True)
    return x.groupby('date')[FIELDS].max().sort_index()

def daily_era5(city):
    d=pd.read_parquet(Path('data/processed')/city/'drivers_rain_daily.parquet')
    d['date']=pd.to_datetime(d.date).dt.normalize();d=d.set_index('date')
    return d[['rain_max_3h_mm_max_cells','rain_total_mm_max_cells','rain_prev_72h_mm_max_cells']].rename(columns=dict(zip(['rain_max_3h_mm_max_cells','rain_total_mm_max_cells','rain_prev_72h_mm_max_cells'],FIELDS)))

def percentile(x):
    out=x.copy();ref={f:np.sort(x[f].dropna().to_numpy(np.float64)) for f in FIELDS}
    for f in FIELDS:
        v=x[f].to_numpy(float);r=ref[f]
        out['q_'+f]=np.searchsorted(r,v,side='right')/max(1,len(r));out.loc[~np.isfinite(v),'q_'+f]=np.nan
    return out,{'n_climatology_days':int(len(x)),'features':{f:{'n':int(len(ref[f])),'min':float(ref[f][0]),'max':float(ref[f][-1])} for f in FIELDS}}

def labels():
    d=pd.read_parquet('data/processed/flood_records.parquet',columns=['city','date','cause','split'],filters=[('split','in',['train','train_undated'])])
    d['date']=pd.to_datetime(d.date,errors='coerce').dt.normalize();return d

def logit_q(q):
    q=np.clip(np.asarray(q,float),.001,.999)
    return np.log(q/(1-q))

def matrices(frame,cols):return np.column_stack([logit_q(frame['q_'+c]) for c in cols]).astype(np.float32)
def add_y(frame,lab,city):
    acc={'rain','combined'};citylab=lab[(lab.city==city)&lab.date.notna()];dates=set(citylab.loc[citylab.cause.isin(acc),'date']);reports=set(citylab.date)
    x=frame.copy();x['positive']=x.index.normalize().isin(dates).astype(np.uint8);x['no_report']=~x.index.normalize().isin(reports);return x
def rainy(frame,city):return frame.index.month.isin(SEASONS[city])

def fit_candidates(cities_frames, lab, cutoff='2023-01-01'):
    candidates=[['rain_max_3h_mm'],['rain_max_3h_mm','rain_total_mm'],['rain_max_3h_mm','rain_total_mm','rain_prev_72h_mm']]
    pooled=[]
    for city,f in cities_frames.items():
        z=add_y(f,lab,city);z=z.loc[(z.index<pd.Timestamp(cutoff))&rainy(z,city)].dropna(subset=['q_'+c for c in FIELDS])
        z['city']=city;pooled.append(z)
    data=pd.concat(pooled);years=sorted(data.index.year.unique());cv={};
    for ci,cols in enumerate(candidates):
        fold=[]
        for year in years:
            tr=data[data.index.year!=year];te=data[data.index.year==year]
            if tr.positive.nunique()<2 or te.positive.nunique()<2:continue
            w=np.where(tr.city.eq('ho_chi_minh'),.5/tr.city.eq('ho_chi_minh').sum(),.5/tr.city.eq('da_nang').sum()).astype(np.float64)
            m=LogisticRegression(C=.1,solver='liblinear',class_weight='balanced',random_state=713,max_iter=300)
            m.fit(matrices(tr,cols),tr.positive.to_numpy(int),sample_weight=w)
            p=m.predict_proba(matrices(te,cols))[:,1];fold.append({'year':int(year),'auc':float(roc_auc_score(te.positive,p)),'ap':float(average_precision_score(te.positive,p)),'n_pos':int(te.positive.sum())})
        cv[str(ci)]={'features':cols,'folds':fold,'mean_auc':float(np.mean([x['auc'] for x in fold])) if fold else np.nan,'mean_ap':float(np.mean([x['ap'] for x in fold])) if fold else np.nan}
    best_i=max(range(len(candidates)),key=lambda i:(cv[str(i)]['mean_auc'] if np.isfinite(cv[str(i)]['mean_auc']) else -1,-i))
    cols=candidates[best_i];w=np.where(data.city.eq('ho_chi_minh'),.5/data.city.eq('ho_chi_minh').sum(),.5/data.city.eq('da_nang').sum()).astype(np.float64)
    model=LogisticRegression(C=.1,solver='liblinear',class_weight='balanced',random_state=713,max_iter=300).fit(matrices(data,cols),data.positive.to_numpy(int),sample_weight=w)
    return data,cols,model,cv

def score(model,cols,frame):
    return model.predict_proba(matrices(frame,cols))[:,1]
def choose_states(data, model, cols):
    z=data.copy();z['T']=score(model,cols,z);pos=z.loc[z.positive==1,'T'].to_numpy();neg=z.loc[z.no_report,'T'].to_numpy()
    if not len(pos) or not len(neg):return {'q_watch':.5,'q_alert':.9,'tradeoff':[],'targets_met':False}
    vals=np.unique(np.quantile(z['T'].to_numpy(float),np.linspace(0,1,201)));curve=[]
    for alert in vals:
        sens=float(np.mean(pos>=alert));quiet=float(np.mean(neg<alert));curve.append({'q_alert':float(alert),'alert_sensitivity':sens,'no_report_quiet':quiet})
    feasible=[r for r in curve if r['alert_sensitivity']>=.60 and r['no_report_quiet']>=.90]
    if feasible:alert=max(feasible,key=lambda r:r['q_alert'])['q_alert']
    else:alert=max(curve,key=lambda r:(min(r['alert_sensitivity']/.60,r['no_report_quiet']/.90),r['alert_sensitivity']+r['no_report_quiet']))['q_alert']
    watches=np.unique(np.quantile(z['T'].to_numpy(float),np.linspace(0,1,201)))
    wopts=[float(q) for q in watches if np.mean(pos>=q)>=.85 and q<=alert]
    watch=max(wopts) if wopts else min(.0,alert)
    return {'q_watch':float(watch),'q_alert':float(alert),'alert_sensitivity':float(np.mean(pos>=alert)),'no_report_quiet':float(np.mean(neg<alert)),'watch_or_alert_sensitivity':float(np.mean(pos>=watch)),'targets_met':bool(np.mean(pos>=alert)>=.60 and np.mean(neg<alert)>=.90 and np.mean(pos>=watch)>=.85),'tradeoff':curve,'n_fit_positive_days':int(len(pos)),'n_fit_no_report_days':int(len(neg))}

def main(pilot=False,cutoff='2023-01-01'):
    OUT.mkdir(parents=True,exist_ok=True);daily={};cdfmeta={}
    for city in CITIES:
        e=daily_era5(city);daily[(city,'era5')],cdfmeta[f'{city}_era5']=percentile(e)
        f=daily_ifs(city,pilot);daily[(city,'ifs')],cdfmeta[f'{city}_ifs']=percentile(f)
        if pilot:
            print('pilot',city,'ERA5',len(e),'IFS',len(f),'peak aggregation sample complete');continue
        for source in ('era5','ifs'):
            daily[(city,source)].rename_axis('date').reset_index().to_parquet(OUT/f'{city}_{source}.parquet',index=False)
    lab=labels();frames={city:daily[(city,'era5')].dropna(subset=['q_'+FIELDS[0]]) for city in CITIES}
    data,cols,model,cv=fit_candidates(frames,lab,cutoff);states=choose_states(data,model,cols)
    if pilot:
        print('pilot trigger fit',cols,states['q_watch'],states['q_alert']);return
    config={'source_percentile_columns':['q_'+x for x in cols],'driver_features':cols,'transform':'clipped logit(q), q clipped to [0.001,0.999]','candidate_cv':cv,'selected_features':cols,'C':.1,'class_weight':'balanced','random_state':713,'coef':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),'n_fit_rows':len(data),'n_fit_positive_days':int(data.positive.sum()),'fit_cutoff':cutoff,'max_fit_date':str(pd.Timestamp(cutoff)-pd.Timedelta(days=1)),'pooled_cities':['ho_chi_minh','da_nang'],'source_for_fit':'ERA5 percentile CDFs','states':states,'label_free_baseline':'sigmoid((q_rain_max_3h_mm-0.95)/0.02)'}
    Path('models/rain_percentile_trigger.json').write_text(json.dumps(config,indent=2))
    for city in CITIES:
        for src in ('era5','ifs'):
            frame=daily[(city,src)].copy();frame['T_rain']=score(model,cols,frame);q=frame['q_rain_max_3h_mm'].to_numpy(float);frame['T_rain_label_free']=1/(1+np.exp(-np.clip((q-.95)/.02,-40,40)));frame.rename_axis('date').reset_index().to_parquet(OUT/f'{city}_{src}.parquet',index=False)
    print(json.dumps({'selected':cols,'states':{k:v for k,v in states.items() if k!='tradeoff'},'cv':cv},indent=2,default=str))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--cutoff',default='2023-01-01');a=p.parse_args();main(a.pilot,a.cutoff)

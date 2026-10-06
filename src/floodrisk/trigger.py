"""Day-level rainfall/tide trigger candidates with FIT-only selection."""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

RAIN_SEASON={'ho_chi_minh':set(range(5,12)),'da_nang':{9,10,11,12}}
RAIN_FEATURES=['rain_max_3h_mm_max_cells','rain_total_mm_max_cells','rain_prev_24h_mm_max_cells','rain_prev_72h_mm_max_cells']

def positive_dates(records,city,cause):
    x=records.loc[(records.city==city)&records.date.notna()].copy()
    accepted={'rain':{'rain','combined'},'tide':{'tide','combined'}}[cause]
    x=x[x.cause.isin(accepted)];return set(pd.to_datetime(x.date).dt.normalize())

def split_day_table(city,cause,drivers,positives):
    d=drivers.copy();d['date']=pd.to_datetime(d.date).dt.normalize();season=d.date.dt.month.isin(RAIN_SEASON[city]);d=d[season|d.date.isin(positives)].copy()
    d['positive']=d.date.isin(positives).astype(np.int8);d['year']=d.date.dt.year
    return d

def _matrix(df,candidate,cause,index=None):
    if cause=='rain':
        if candidate=='logit_design':cols=[RAIN_FEATURES[0],RAIN_FEATURES[2]];return df[cols].astype(float),cols
        if candidate=='logit_log':cols=[RAIN_FEATURES[0],RAIN_FEATURES[1],RAIN_FEATURES[3]];return np.log1p(df[cols].clip(lower=0).astype(float)),cols
        col=index or RAIN_FEATURES[0];return pd.DataFrame({col:pd.to_numeric(df[col],errors='coerce')},index=df.index),[col]
    col='astro_daily_max_m';return pd.DataFrame({col:pd.to_numeric(df[col],errors='coerce')},index=df.index),[col]

def _fit_logistic(x,y):
    y=np.asarray(y,int)
    if len(np.unique(y))<2:return {'kind':'constant','value':float(y.mean() if len(y) else 0.)}
    model=make_pipeline(SimpleImputer(strategy='median',add_indicator=False),StandardScaler(),LogisticRegression(C=1.,max_iter=1000,solver='lbfgs'))
    model.fit(x,y);sc=model.named_steps['standardscaler'];lr=model.named_steps['logisticregression']
    return {'kind':'logistic','mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'coef':lr.coef_[0].tolist(),'intercept':float(lr.intercept_[0]),'features':list(x.columns)}

def _apply(param,x):
    if param['kind']=='constant':return np.full(len(x),param['value'],np.float32)
    if param['kind']=='logistic':
        q=x[param['features']].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        if param.get('candidate')=='logit_log':q=np.log1p(np.maximum(q,0))
        a=np.where(np.isfinite(q),q,np.asarray(param['mean'])[None,:]);z=((a-np.asarray(param['mean']))/np.asarray(param['scale']))@np.asarray(param['coef'])+param['intercept'];return expit(z).astype(np.float32)
    if param['kind']=='isotonic':
        return np.interp(x[param['feature']].to_numpy(float),param['x_thresholds'],param['y_thresholds'],left=param['y_thresholds'][0],right=param['y_thresholds'][-1]).astype(np.float32)
    if param['kind']=='percentile':
        values=np.asarray(param['climatology_q'],float);q=np.linspace(0,1,len(values));p=np.interp(x[param['feature']].to_numpy(float),values,q,left=0,right=1);return expit((p-.95)/.02).astype(np.float32)
    if param['kind']=='zero':return np.zeros(len(x),np.float32)
    raise ValueError(param['kind'])

def _fit_iso(x,y,col):
    q=pd.to_numeric(x[col],errors='coerce').to_numpy(float);ok=np.isfinite(q)
    if len(np.unique(y[ok]))<2 or len(np.unique(q[ok]))<2:return {'kind':'constant','value':float(np.mean(y[ok]) if ok.any() else 0.)}
    iso=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(q[ok],y[ok]);return {'kind':'isotonic','feature':col,'x_thresholds':iso.X_thresholds_.tolist(),'y_thresholds':iso.y_thresholds_.tolist()}

def _climatology(x,col):
    v=pd.to_numeric(x[col],errors='coerce').dropna().to_numpy(float)
    return {'kind':'percentile','feature':col,'climatology_q':np.quantile(v,np.linspace(0,1,201)).tolist() if len(v) else [0.]}

def _metric(y,p):
    y=np.asarray(y,bool);p=np.asarray(p,float)
    if not y.any() or y.all():return {'auc':np.nan,'ap':np.nan}
    return {'auc':float(roc_auc_score(y,p)),'ap':float(average_precision_score(y,p))}

def bootstrap_ci(y,p,draws=500,seed=406):
    y=np.asarray(y,bool);p=np.asarray(p,float);point=_metric(y,p);pos=np.flatnonzero(y);neg=np.flatnonzero(~y);rng=np.random.default_rng(seed);values={'auc':[],'ap':[]}
    for _ in range(draws):
        if not len(pos) or not len(neg):continue
        ix=np.r_[rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)];m=_metric(y[ix],p[ix])
        for k,v in m.items():values[k].append(v)
    ci={k:np.quantile(v,[.025,.975]).tolist() if v else [np.nan,np.nan] for k,v in values.items()};return point,ci

def _candidate_names(cause):return ['logit_design','logit_log','isotonic','percentile'] if cause=='rain' else ['logit_tide','percentile']

def _candidate_param(name,train,cause,index=None):
    y=train.positive.to_numpy(int)
    if name in ('logit_design','logit_log','logit_tide'):
        x,cols=_matrix(train,name,cause);p=_fit_logistic(x,y);p.update(candidate=name,features=cols);return p
    if name=='percentile':
        col=RAIN_FEATURES[0] if cause=='rain' else 'astro_daily_max_m';p=_climatology(train,col);p['candidate']=name;return p
    if name=='isotonic':
        col=index or RAIN_FEATURES[0];p=_fit_iso(_matrix(train,'index',cause,col)[0],y,col);p.update(candidate=name,selected_index=col);return p
    raise ValueError(name)

def crossval_candidates(table,cause):
    fit=table.loc[table.date<'2023-01-01'].dropna(subset=([*RAIN_FEATURES] if cause=='rain' else ['astro_daily_max_m'])).copy()
    y=fit.positive.to_numpy(int);years=fit.year.to_numpy();pred={n:np.full(len(fit),np.nan,np.float32) for n in _candidate_names(cause)}
    unique=np.unique(years)
    for yr in unique:
        tr=fit.year!=yr;te=~tr
        if not te.any() or len(np.unique(y[tr]))<2:continue
        # The isotonic index is selected only from each fold's training years.
        idx=RAIN_FEATURES[:3] if cause=='rain' else []
        bestidx=None
        if cause=='rain':
            scores=[]
            for col in idx:
                x=fit.loc[tr,[col]].astype(float);m=_fit_logistic(x,fit.loc[tr,'positive']);scores.append((_metric(fit.loc[tr,'positive'],_apply(m,fit.loc[tr,[col]]))['auc'],col))
            bestidx=max(scores,key=lambda z:(np.nan_to_num(z[0],nan=-1),z[1]))[1] if scores else RAIN_FEATURES[0]
        for name in _candidate_names(cause):
            model=_candidate_param(name,fit.loc[tr],cause,bestidx)
            if name in ('logit_design','logit_log','logit_tide'):x=fit.loc[te]
            elif name=='isotonic':x,_=_matrix(fit.loc[te],'index',cause,model['selected_index'])
            else:x=fit.loc[te]
            pred[name][np.flatnonzero(te)]=_apply(model,x)
    metrics={}
    for n,p in pred.items():
        ok=np.isfinite(p);metrics[n]=bootstrap_ci(y[ok],p[ok],draws=500,seed=406+len(n)) if ok.any() else ({'auc':np.nan,'ap':np.nan},{'auc':[np.nan,np.nan],'ap':[np.nan,np.nan]})
    return fit,pred,metrics

def fit_selected(table,cause,cv_metrics):
    names=_candidate_names(cause);valid=[n for n in names if np.isfinite(cv_metrics[n][0]['auc'])]
    chosen=max(valid,key=lambda n:(cv_metrics[n][0]['auc'],cv_metrics[n][0]['ap'])) if valid else 'percentile'
    fit=table.loc[table.date<'2023-01-01'].dropna(subset=([*RAIN_FEATURES] if cause=='rain' else ['astro_daily_max_m'])).copy()
    bestidx=None
    if chosen=='isotonic':
        vals=[]
        for col in RAIN_FEATURES[:3]:
            x=fit[[col]].astype(float);m=_fit_logistic(x,fit.positive);vals.append((_metric(fit.positive,_apply(m,x))['auc'],col))
        bestidx=max(vals,key=lambda z:(np.nan_to_num(z[0],nan=-1),z[1]))[1]
    param=_candidate_param(chosen,fit,cause,bestidx)
    param.update(cause=cause,fit_start=str(fit.date.min().date()) if len(fit) else None,fit_end=str(fit.date.max().date()) if len(fit) else None,max_training_date=str(fit.date.max().date()) if len(fit) else None,n_fit_days=int(len(fit)),n_fit_positive_days=int(fit.positive.sum()),fit_years=sorted(map(int,fit.year.unique())))
    return param,fit

def reliability_table(y,p,bins=5):
    d=pd.DataFrame({'y':np.asarray(y,int),'p':np.asarray(p,float)}).dropna()
    if d.empty:return []
    d['bin']=pd.qcut(d.p.rank(method='first'),q=min(bins,len(d)),labels=False,duplicates='drop')
    return [{'bin':int(k),'n':len(g),'mean_p':float(g.p.mean()),'observed_rate':float(g.y.mean())} for k,g in d.groupby('bin')]

def save_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(obj,indent=2,allow_nan=True))

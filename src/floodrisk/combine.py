"""Fit FIT-only route susceptibility and combine it separably with daily triggers."""
from __future__ import annotations
import importlib.util,json
from pathlib import Path
import sys
import numpy as np,pandas as pd

def _best_scorer():
    return Path('models/m1_best.txt').read_text().strip()

def _scorer(name):
    root=str(Path.cwd())
    if root not in sys.path:sys.path.insert(0,root)
    p=Path('experiments/m1')/(name+'.py');spec=importlib.util.spec_from_file_location('m1_combiner',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def _manifest(city):return json.loads((Path('data/processed')/city/'feature_manifest.json').read_text())

def _sample_training_routes(x,positives,known,city,seed=50723):
    """Keep all positives/known reports and cap sampled unlabeled routes at 20k."""
    u=x.in_universe.astype(bool).to_numpy();route=x.route_id.astype(str)
    positive=route.isin(positives).to_numpy()&u;reported=route.isin(known).to_numpy()&u
    unlabeled=np.flatnonzero(u&~reported&~positive)
    rng=np.random.default_rng(seed+(0 if city=='ho_chi_minh' else 1))
    chosen=rng.choice(unlabeled,size=min(20_000,len(unlabeled)),replace=False) if len(unlabeled)>20_000 else unlabeled
    keep=np.flatnonzero((positive|reported)&u)
    keep=np.unique(np.r_[keep,chosen])
    out=x.iloc[keep].copy().reset_index(drop=True)
    meta=pd.DataFrame({'label':out.route_id.astype(str).isin(positives).to_numpy(np.int8),'sample_weight':np.where(out.route_id.astype(str).isin(known),1.,.2).astype(np.float32)})
    out=pd.concat([out,meta],axis=1)
    return out

def read_fit_records(root=Path('.')):
    rec=pd.read_parquet(root/'data/processed/flood_records.parquet',columns=['record_id','city','date','cause','split'],filters=[('split','in',['train','train_undated'])])
    rec['date']=pd.to_datetime(rec.date,errors='coerce');return rec

def join_matched_records(records,root=Path('.')):
    import pyarrow.dataset as ds
    ids=records.record_id.astype(str).drop_duplicates().tolist();path=root/'data/processed/flood_record_matches.parquet';dataset=ds.dataset(path,format='parquet')
    tab=dataset.to_table(columns=['record_id','route_id'],filter=ds.field('record_id').isin(ids))
    matched=tab.to_pandas();matched=matched.dropna(subset=['route_id']);matched['record_id']=matched.record_id.astype(str);matched['route_id']=matched.route_id.astype(str)
    return records.merge(matched,on='record_id',how='inner',validate='one_to_many')

def fit_route_models(root=Path('.'),pilot=False,save=True,cutoff='2023-01-01'):
    name=_best_scorer();scorer=_scorer(name);rec=read_fit_records(root);joined=join_matched_records(rec,root)
    fit=joined[(joined.date<pd.Timestamp(cutoff))|joined.split.eq('train_undated')].copy()
    fit=fit[fit.date.isna()| (fit.date<pd.Timestamp(cutoff))]
    features={};training={};
    for city in ('ho_chi_minh','da_nang'):
        manifest_city=_manifest(city)
        cols=list(dict.fromkeys(['route_id','in_universe']+list(manifest_city['feature_names'])))
        source=root/'data/processed'/city/'route_features.parquet'
        if pilot:
            import pyarrow.parquet as pq
            batches=pq.ParquetFile(source).iter_batches(batch_size=1500,columns=cols)
            parts=[]
            for batch in batches:
                parts.append(batch.to_pandas())
                if sum(map(len,parts))>=6000:break
            x=pd.concat(parts,ignore_index=True).head(6000).copy()
        else:x=pd.read_parquet(source,columns=cols)
        x['route_id']=x.route_id.astype(str)
        for col in x.columns:
            if col not in ('route_id','road_highway_class') and pd.api.types.is_numeric_dtype(x[col]):x[col]=x[col].astype(np.float32)
        x=x.copy()
        features[city]=x
        if pilot:
            n=len(x);meta=pd.DataFrame({'label':(np.arange(n)%67==0).astype(np.int8),'sample_weight':np.ones(n,np.float32)});x=pd.concat([x.reset_index(drop=True),meta],axis=1);training[city]=x[x.in_universe.astype(bool)].copy();continue
        fc=fit[fit.city==city];any_routes=set(fc.route_id.astype(str));
        rain_routes=set(fc.loc[fc.cause.isin(['rain','combined']),'route_id'].astype(str));tide_routes=set(fc.loc[fc.cause.isin(['tide','combined']),'route_id'].astype(str))
        training[city]=_sample_training_routes(x,rain_routes,any_routes,city)
        training[city].attrs['tide_routes']=tide_routes;training[city].attrs['any_routes']=any_routes
    rain_parts=[]
    for city,x in training.items():
        w=x.sample_weight.to_numpy(np.float64);total=max(w.sum(),1.);x=x.copy();x['sample_weight']=(w/total*.5*len(w)).astype(np.float32);rain_parts.append(x)
    rain_train=pd.concat(rain_parts,ignore_index=True);manifest=_manifest('ho_chi_minh')
    rain_model=scorer.fit(rain_train,manifest,'ever_flood_rain')
    tide_model=None
    if not pilot:
        tx=_sample_training_routes(features['ho_chi_minh'],training['ho_chi_minh'].attrs['tide_routes'],training['ho_chi_minh'].attrs['any_routes'],'ho_chi_minh',seed=81023)
        tide_model=scorer.fit(tx,manifest,'ever_flood_tide')
    if save and not pilot:
        Path('models').mkdir(exist_ok=True)
        for kind,m in [('rain',rain_model),('tide',tide_model)]:
            if m is None:continue
            lm=m.get('model') if isinstance(m,dict) else m
            if hasattr(lm,'booster_'):lm.booster_.save_model(f'models/m1_s_{kind}.txt')
        meta={'scorer':name,'fit_cutoff':cutoff,'max_training_date':str(pd.Timestamp(cutoff)-pd.Timedelta(days=1)),'train_cities':['ho_chi_minh','da_nang'],'route_labels':f'dates<{cutoff} plus train_undated','city_balanced_rain':True,'unlabeled_route_cap_per_city':20000,'fixed_seed':50723,'n_fit_routes':{c:int(len(x)) for c,x in training.items()},'n_rain_positive_routes':{c:int(x.label.sum()) for c,x in training.items()},'n_unlabeled_sampled':{c:int((~x.route_id.isin(x.attrs.get('any_routes',set()))).sum()) for c,x in training.items()}}
        Path('models/m1_s_fit_metadata.json').write_text(json.dumps(meta,indent=2))
    return scorer,manifest,features,training,rain_model,tide_model

def percentile_score(raw,universe):
    ref=np.sort(np.asarray(raw,dtype=np.float32)[np.asarray(universe,bool)])
    score=np.searchsorted(ref,np.asarray(raw,dtype=np.float32),side='right').astype(np.float32)/(len(ref)+1.)
    score[~np.asarray(universe,bool)]*=.5
    return score

def route_trigger(rain_s,tide_s,t_rain,t_tide):
    sr=np.asarray(rain_s,np.float32);st=np.asarray(tide_s,np.float32)
    tr=np.float32(t_rain);tt=np.float32(t_tide)
    return np.asarray(1.-(1.-sr*tr)*(1.-st*tt),np.float32)

def history_scores(joined,city,routes,cutoff='2023-01-01'):
    x=joined[(joined.city==city)&(joined.date.isna()|(joined.date<pd.Timestamp(cutoff)))]
    out={}
    for cause,causes in [('rain',{'rain','combined'}),('tide',{'tide','combined'})]:
        g=x[x.cause.isin(causes)]
        counts=g.dropna(subset=['date']).groupby('route_id').date.nunique().to_dict()
        seen=set(g.route_id.astype(str));n=np.asarray([int(counts.get(r,0)) for r in routes],np.float32)
        flag=np.asarray([r in seen for r in routes])
        value=np.where(flag,.9+.1*np.minimum(1.,n/3.),0.).astype(np.float32)
        out[cause]=(value,flag,n)
    return out

def route_bands(score,tie,mask):
    ids=np.flatnonzero(np.asarray(mask,bool));state=np.zeros(len(mask),np.uint8)
    if not len(ids):return state
    order=np.lexsort((-np.asarray(tie)[ids],-np.asarray(score)[ids]))
    a=max(1,int(np.ceil(.05*len(ids))));b=max(a,int(np.ceil(.20*len(ids))))
    state[ids[order[:a]]]=2;state[ids[order[a:b]]]=1
    return state

def choose_day_thresholds(city,cause,trigger,records):
    col='T_'+cause;fit=trigger.loc[trigger.index<pd.Timestamp('2023-01-01')]
    r=records[(records.city==city)&records.date.notna()&(records.date<pd.Timestamp('2023-01-01'))]
    accepted={'rain':{'rain','combined'},'tide':{'tide','combined'}}[cause]
    posdays=set(pd.to_datetime(r.loc[r.cause.isin(accepted),'date']).dt.normalize())
    monthset=set(range(5,12)) if city=='ho_chi_minh' else {9,10,11,12}
    any_report_days=set(pd.to_datetime(r.date.dropna()).dt.normalize())
    seasonal=fit.index.month.isin(monthset);negdays=set(fit.index[seasonal])-any_report_days
    pos=fit.loc[fit.index.isin(posdays),col].dropna().to_numpy(float)
    neg=fit.loc[fit.index.isin(negdays),col].dropna().to_numpy(float)
    vals=fit[col].dropna().to_numpy(float)
    if not len(pos) or not len(neg) or not len(vals):
        return {'t_lo':1.000001,'t_hi':1.000002,'n_fit_positive_days':len(pos),'n_fit_no_report_days':len(neg),'targets_met':False,'selected_alert_sensitivity':0.,'selected_quiet_specificity':0.,'tradeoff':[]}
    his=np.unique(np.quantile(vals,np.linspace(0,1,101)));min_gap=max(1e-6,.01*float(np.max(vals)-np.min(vals)))
    curve=[];pairs=[]
    for hi in his:
        sens=float(np.mean(pos>=hi));ceiling=hi-min_gap
        low_opts=np.unique(np.r_[neg[neg<=ceiling],np.nextafter(ceiling,-np.inf)])
        low_opts=low_opts[low_opts<hi]
        quiet=np.asarray([np.mean(neg<lo) for lo in low_opts]) if len(low_opts) else np.asarray([0.])
        bestq=float(quiet.max());bestlo=float(low_opts[np.flatnonzero(quiet==bestq)[-1]]) if len(low_opts) else float(np.nextafter(hi,-np.inf))
        curve.append({'t_hi':float(hi),'t_lo_for_best_quiet':bestlo,'min_gap':min_gap,'alert_sensitivity':sens,'quiet_specificity':bestq})
        pairs.append((float(hi),bestlo,sens,bestq))
    feasible=[p for p in pairs if p[2]>=.70 and p[3]>=.80]
    if feasible:chosen=max(feasible,key=lambda p:(p[0],p[3],p[2]))
    else:chosen=max(pairs,key=lambda p:(min(p[2]/.70,p[3]/.80),p[2]+p[3],p[0]))
    hi,lo,sens,quiet=chosen
    return {'t_lo':lo,'t_hi':hi,'n_fit_positive_days':len(pos),'n_fit_no_report_days':len(neg),'targets_met':bool(sens>=.70 and quiet>=.80),'selected_alert_sensitivity':sens,'selected_quiet_specificity':quiet,'tradeoff':curve}

def day_state(t,threshold):
    if t>=threshold['t_hi']:return 2
    if t>=threshold['t_lo']:return 1
    return 0

def levels_from_bands(rain_band,tide_band,t_rain,t_tide,thresholds):
    result=np.zeros(len(rain_band),np.uint8)
    for band,t,cause in ((rain_band,t_rain,'rain'),(tide_band,t_tide,'tide')):
        ds=day_state(float(t),thresholds[cause])
        if ds==2:lev=np.where(band==2,2,np.where(band==1,1,0))
        elif ds==1:lev=np.where(band==2,1,0)
        else:lev=np.zeros(len(band),np.uint8)
        result=np.maximum(result,lev.astype(np.uint8))
    return result

def _triggers(city,root=Path('.')):
    x=pd.read_parquet(root/'data/processed'/city/'trigger_daily.parquet',columns=['date','T_tide'])
    x['date']=pd.to_datetime(x.date).dt.normalize();x=x.set_index('date')
    for source in ('era5','ifs'):
        r=pd.read_parquet(root/'data/processed/rain_percentiles'/f'{city}_{source}.parquet',columns=['date','T_rain'])
        r['date']=pd.to_datetime(r.date).dt.normalize();r=r.set_index('date').rename(columns={'T_rain':f'T_rain_{source}'})
        x=x.join(r,how='left')
    return x

def build_combination(root=Path('.'),pilot=False,save=True,cutoff='2023-01-01'):
    scorer,manifest,features,training,rain_model,tide_model=fit_route_models(root,pilot=pilot,save=save,cutoff=cutoff)
    if pilot:
        return {'best':_best_scorer(),'pilot_rows':{c:len(x) for c,x in features.items()},'training_rows':{c:len(x) for c,x in training.items()}}
    rec=read_fit_records(root);rec=rec[rec.date.isna()|(rec.date<pd.Timestamp(cutoff))].copy();joined=join_matched_records(rec,root)
    models={};thresholds={}
    for city,ft0 in features.items():
        ft=ft0.reset_index(drop=True);route=ft.route_id.astype(str).to_numpy();uni=ft.in_universe.to_numpy(bool)
        sm_r=.9*percentile_score(scorer.predict(rain_model,ft),uni)
        sm_t=.9*percentile_score(scorer.predict(tide_model,ft),uni) if city=='ho_chi_minh' else np.zeros(len(ft),np.float32)
        hist=history_scores(joined,city,route,cutoff=cutoff);sh_r=np.maximum(sm_r,hist['rain'][0]);sh_t=np.maximum(sm_t,hist['tide'][0])
        out=ft[['route_id','in_universe']].copy()
        out['S_rain']=sm_r;out['S_tide']=sm_t;out['S_hyb_rain']=sh_r;out['S_hyb_tide']=sh_t
        out['S_hist_rain']=hist['rain'][0];out['S_hist_tide']=hist['tide'][0]
        out['H_rain']=hist['rain'][1].astype(np.uint8);out['H_tide']=hist['tide'][1].astype(np.uint8);out['H_any']=(hist['rain'][1]|hist['tide'][1]).astype(np.uint8)
        out['n_distinct_dates_rain']=hist['rain'][2].astype(np.uint16);out['n_distinct_dates_tide']=hist['tide'][2].astype(np.uint16)
        out.to_parquet(root/'data/processed'/city/'route_susceptibility.parquet',index=False)
        trig=_triggers(city,root)
        old_thresholds=json.loads(Path('models/combination_thresholds.json').read_text())['thresholds'][city]
        pcfg=json.loads(Path('models/rain_percentile_trigger.json').read_text())
        thresholds[city]={'rain':{'t_lo':pcfg['states']['q_watch'],'t_hi':pcfg['states']['q_alert'],'targets_met':pcfg['states']['targets_met'],'selected_alert_sensitivity':pcfg['states']['alert_sensitivity'],'selected_quiet_specificity':pcfg['states']['no_report_quiet'],'source':'pooled percentile trigger'},'tide':old_thresholds['tide']}
        models[city]=(out,route,uni,sm_r,sm_t,sh_r,sh_t,hist,trig)
    Path('models').mkdir(exist_ok=True)
    Path('models/combination_thresholds.json').write_text(json.dumps({'max_fit_date':'2022-12-31','rule':'T<t_lo quiet; t_lo<=T<t_hi watch; T>=t_hi alert; A=top5%, B=next15% by cause-specific hybrid score','targets':{'alert_sensitivity':.70,'quiet_specificity':.80},'thresholds':thresholds,'rain_percentile_thresholds':json.loads(Path('models/rain_percentile_trigger.json').read_text())['states']},indent=2))
    h0_path=Path('models/m2_history_h0.json')
    if h0_path.exists():h0_path.write_text(json.dumps({'superseded_by':'combination_thresholds.json','history_score':'0.90 + 0.10*min(1,n_distinct_dates/3)','h0':None},indent=2))
    route_summary={}; dev_days={}
    for city,(out,route,uni,sm_r,sm_t,sh_r,sh_t,hist,trig) in models.items():
        daily=[];tdev=trig[(trig.index>='2023-01-01')&(trig.index<'2025-01-01')]
        for dt,q in tdev.iterrows():
            row={'date':dt};hm=hist['rain'][1]|hist['tide'][1]
            for source in ('era5','ifs'):
                tr=float(getattr(q,f'T_rain_{source}'));tt=float(q.T_tide)
                for scope,mask in [('all',np.ones(len(route),bool)),('universe',uni)]:
                    modellev=levels_from_bands(route_bands(sm_r,sm_r,mask),route_bands(sm_t,sm_t,mask),tr,tt,thresholds[city])
                    hyblev=levels_from_bands(route_bands(sh_r,sm_r,mask),route_bands(sh_t,sm_t,mask),tr,tt,thresholds[city])
                    row[f'model_alert_{scope}_{source}']=float(np.mean(modellev[mask]>=1))
                    row[f'hybrid_alert_{scope}_{source}']=float(np.mean(hyblev[mask]>=1))
                    row[f'history_alert_{scope}_{source}']=float(np.mean(hm[mask]))
                pm=route_trigger(sm_r,sm_t,tr,tt);ph=route_trigger(sh_r,sh_t,tr,tt)
                row[f'P_model_mean_{source}']=float(np.mean(pm));row[f'P_hybrid_mean_{source}']=float(np.mean(ph))
            daily.append(row)
        pd.DataFrame(daily).to_parquet(root/'data/processed'/city/'daily_alert_index_dev.parquet',index=False)
        route_summary[city]={'total':len(route),'in_universe':int(uni.sum()),'fit_routes':len(training[city]),'fit_unlabeled_sampled':int((~training[city].route_id.isin(training[city].attrs.get('any_routes',set()))).sum())}
        dev_days[city]=len(tdev)
    return {'best':_best_scorer(),'routes':route_summary,'thresholds':{c:{cause:{k:v for k,v in params.items() if k!='tradeoff'} for cause,params in cs.items()} for c,cs in thresholds.items()},'dev_alert_days':dev_days,'fit_cutoff':'2022-12-31'}

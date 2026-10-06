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

def read_fit_records(root=Path('.')):
    rec=pd.read_parquet(root/'data/processed/flood_records.parquet',columns=['record_id','city','date','cause','split'],filters=[('split','in',['train','train_undated'])])
    rec['date']=pd.to_datetime(rec.date,errors='coerce');return rec

def join_matched_records(records,root=Path('.')):
    import pyarrow.dataset as ds
    ids=records.record_id.astype(str).drop_duplicates().tolist();path=root/'data/processed/flood_record_matches.parquet';dataset=ds.dataset(path,format='parquet')
    tab=dataset.to_table(columns=['record_id','route_id'],filter=ds.field('record_id').isin(ids))
    matched=tab.to_pandas();matched=matched.dropna(subset=['route_id']);matched['record_id']=matched.record_id.astype(str);matched['route_id']=matched.route_id.astype(str)
    return records.merge(matched,on='record_id',how='inner',validate='one_to_many')

def fit_route_models(root=Path('.'),pilot=False,save=True):
    name=_best_scorer();scorer=_scorer(name);rec=read_fit_records(root);joined=join_matched_records(rec,root)
    fit=joined[(joined.date<pd.Timestamp('2023-01-01'))|joined.split.eq('train_undated')].copy()
    fit=fit[fit.date.isna()| (fit.date<pd.Timestamp('2023-01-01'))]
    features={};training={};
    for city in ('ho_chi_minh','da_nang'):
        manifest_city=_manifest(city)
        cols=['route_id','in_universe']+list(manifest_city['feature_names'])
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
        x['route_id']=x.route_id.astype(str);features[city]=x
        if pilot:
            n=len(x);x['label']=(np.arange(n)%67==0).astype(np.int8);x['sample_weight']=1.;training[city]=x[x.in_universe.astype(bool)].copy();continue
        fc=fit[fit.city==city];any_routes=set(fc.route_id.astype(str));
        rain_routes=set(fc.loc[fc.cause.isin(['rain','combined']),'route_id'].astype(str));tide_routes=set(fc.loc[fc.cause.isin(['tide','combined']),'route_id'].astype(str))
        x['label']=x.route_id.isin(rain_routes).astype(np.int8);x['sample_weight']=np.where(x.route_id.isin(any_routes),1.,.2).astype(np.float32)
        training[city]=x[x.in_universe.astype(bool)].copy();training[city].attrs['tide_routes']=tide_routes;training[city].attrs['any_routes']=any_routes
    rain_parts=[]
    for city,x in training.items():
        w=x.sample_weight.to_numpy(np.float64);total=max(w.sum(),1.);x=x.copy();x['sample_weight']=(w/total*.5*len(w)).astype(np.float32);rain_parts.append(x)
    rain_train=pd.concat(rain_parts,ignore_index=True);manifest=_manifest('ho_chi_minh')
    rain_model=scorer.fit(rain_train,manifest,'ever_flood_rain')
    tide_model=None
    if not pilot:
        tx=training['ho_chi_minh'].copy();tide_routes=tx.attrs['tide_routes'];any_routes=tx.attrs['any_routes'];tx['label']=tx.route_id.isin(tide_routes).astype(np.int8);tx['sample_weight']=np.where(tx.route_id.isin(any_routes),1.,.2).astype(np.float32);tide_model=scorer.fit(tx,manifest,'ever_flood_tide')
    if save and not pilot:
        Path('models').mkdir(exist_ok=True)
        for kind,m in [('rain',rain_model),('tide',tide_model)]:
            if m is None:continue
            lm=m.get('model') if isinstance(m,dict) else m
            if hasattr(lm,'booster_'):lm.booster_.save_model(f'models/m1_s_{kind}.txt')
        meta={'scorer':name,'fit_cutoff':'2022-12-31','max_training_date':'2022-12-31','train_cities':['ho_chi_minh','da_nang'],'route_labels':'dates<2023 plus train_undated','city_balanced_rain':True,'n_fit_routes':{c:int(len(x)) for c,x in training.items()}}
        Path('models/m1_s_fit_metadata.json').write_text(json.dumps(meta,indent=2))
    return scorer,manifest,features,training,rain_model,tide_model

def percentile_score(raw,universe):
    ref=np.sort(np.asarray(raw,dtype=np.float32)[np.asarray(universe,bool)]);score=np.asarray(raw,dtype=np.float32);return np.searchsorted(ref,score,side='right').astype(np.float32)/(len(ref)+1.)

def route_trigger(rain_s,tide_s,t_rain,t_tide,h_rain=None,h_tide=None,h0=0.):
    sr=np.asarray(rain_s,np.float32);st=np.asarray(tide_s,np.float32);hr=np.zeros_like(sr) if h_rain is None else np.asarray(h_rain,np.float32);ht=np.zeros_like(st) if h_tide is None else np.asarray(h_tide,np.float32)
    tr=np.float32(t_rain);tt=np.float32(t_tide)
    p=1.-(1.-sr*tr)*(1.-st*tt);hybr=1.-(1.-np.maximum(sr,h0*hr)*tr)*(1.-np.maximum(st,h0*ht)*tt)
    return np.asarray(p,np.float32),np.asarray(hybr,np.float32)

def levels(scores,fit_event_day_values):
    x=np.asarray(fit_event_day_values,dtype=np.float32);x=x[np.isfinite(x)]
    if not len(x):return {'medium':1.,'high':1.}
    return {'medium':float(np.quantile(x,.80)),'high':float(np.quantile(x,.95))}

def _train_history(joined,city,excluded_year=None):
    x=joined[joined.city==city]
    if excluded_year is not None:x=x[x.date.isna()|(x.date.dt.year!=excluded_year)]
    fit=x[x.date.isna()|(x.date<pd.Timestamp('2023-01-01'))]
    rain=set(fit.loc[fit.cause.isin(['rain','combined']),'route_id'].astype(str));tide=set(fit.loc[fit.cause.isin(['tide','combined']),'route_id'].astype(str))
    anyr=set(fit.route_id.astype(str));return rain,tide,anyr

def _triggers(city,root=Path('.')):
    x=pd.read_parquet(root/'data/processed'/city/'trigger_daily.parquet');x['date']=pd.to_datetime(x.date).dt.normalize();return x.set_index('date')

def choose_h0(city,joined,route,sr,st,univ,trigger,grid=(0.,.25,.5,.75,1.)):
    fit=joined[(joined.city==city)&(joined.date.notna())&(joined.date<pd.Timestamp('2023-01-01'))]
    groups=fit.groupby('date',sort=True);scores={float(h):[] for h in grid};idx=pd.Index(route)
    for date,g in groups:
        if date not in trigger.index:continue
        year=pd.Timestamp(date).year;hr,ht,_=_train_history(joined,city,year)
        row=trigger.loc[date];tr=float(row.get('T_rain',0) or 0);tt=float(row.get('T_tide',0) or 0)
        pos=set(g.loc[g.cause.isin(['rain','combined','tide']),'route_id'].astype(str));pos_ix=np.flatnonzero(np.asarray(idx.isin(pos))&univ)
        if not len(pos_ix):continue
        hrv=np.asarray(idx.isin(hr),np.float32);htv=np.asarray(idx.isin(ht),np.float32)
        for h0 in grid:
            _,ph=route_trigger(sr,st,tr,tt,hrv,htv,h0);ids=np.flatnonzero(univ);k=max(1,int(np.ceil(.20*len(ids))));order=ids[np.argsort(ph[ids],kind='stable')[::-1][:k]]
            scores[float(h0)].append(float(np.isin(pos_ix,order).sum()/len(pos_ix)))
    means={str(h):float(np.mean(v)) if v else 0. for h,v in scores.items()};best=max(scores,key=lambda h:(means[str(h)],-h));return best,means

def build_combination(root=Path('.'),pilot=False,save=True):
    scorer,manifest,features,training,rain_model,tide_model=fit_route_models(root,pilot=pilot,save=save)
    if pilot:return {'best':_best_scorer(),'pilot_rows':{c:len(x) for c,x in features.items()},'training_rows':{c:len(x) for c,x in training.items()}}
    rec=read_fit_records(root);joined=join_matched_records(rec,root)
    fit=joined[joined.date.isna()|(joined.date<pd.Timestamp('2023-01-01'))]
    scores={};trig={};h0meta={}
    for city,ft in features.items():
        rawr=scorer.predict(rain_model,ft,manifest);sr=percentile_score(rawr,ft.in_universe.astype(bool))
        if city=='ho_chi_minh':rawt=scorer.predict(tide_model,ft,manifest);st=percentile_score(rawt,ft.in_universe.astype(bool))
        else:st=np.zeros(len(ft),np.float32)
        route=ft.route_id.astype(str).to_numpy();uni=ft.in_universe.to_numpy(bool);hr,ht,_=_train_history(joined,city)
        hrv=np.isin(route,list(hr));htv=np.isin(route,list(ht));out=ft[['route_id','in_universe']].copy()
        out['S_rain']=sr;out['S_tide']=st;out['H_rain']=hrv.astype(np.uint8);out['H_tide']=htv.astype(np.uint8);out['H_any']=(hrv|htv).astype(np.uint8)
        roads=pd.read_parquet(root/'data/processed'/city/'routes.parquet',columns=['route_id','highway_class']);roads['route_id']=roads.route_id.astype(str);out=out.merge(roads,on='route_id',how='left',validate='one_to_one')
        out.to_parquet(root/'data/processed'/city/'route_susceptibility.parquet',index=False);scores[city]=(out,route,sr.astype(np.float32),st.astype(np.float32),uni,hrv.astype(np.float32),htv.astype(np.float32))
        trig[city]=_triggers(city,root)
    for city,(out,route,sr,st,uni,hrv,htv) in scores.items():
        h0,selection=choose_h0(city,joined,route,sr,st,uni,trig[city]);h0meta[city]={'h0':h0,'fit_cv_mean_top20_hit':selection,'selection_uses':'FIT flood dates; leave-event-year-out history flags; base M1/T fit on FIT only'}
    Path('models').mkdir(exist_ok=True);Path('models/m2_history_h0.json').write_text(json.dumps({'max_fit_date':'2022-12-31','selection':h0meta},indent=2))
    # Calibration days come from all eligible dated FIT records, including
    # reports that could not be matched to an OSM route.
    thresholds={};event_dates={c:sorted(pd.to_datetime(rec.loc[(rec.city==c)&rec.date.notna()&(rec.date<pd.Timestamp('2023-01-01')),'date']).dt.normalize().unique()) for c in scores}
    alerts={}
    for city,(out,route,sr,st,uni,hrv,htv) in scores.items():
        h0=h0meta[city]['h0'];base_all=[];base_uni=[];hyb_all=[];hyb_uni=[]
        for dt in event_dates[city]:
            if dt not in trig[city].index:continue
            q=trig[city].loc[dt];p,ph=route_trigger(sr,st,q.T_rain,q.T_tide,hrv,htv,h0)
            base_all.append(p);base_uni.append(p[uni]);hyb_all.append(ph);hyb_uni.append(ph[uni])
        thresholds[city]={}
        for scope,base,hyb in [('all',base_all,hyb_all),('universe',base_uni,hyb_uni)]:
            thresholds[city][scope]={'model':levels(None,np.concatenate(base) if base else []),'hybrid':levels(None,np.concatenate(hyb) if hyb else [])}
        # DEV daily alert indices are computed one day at a time, never route×day materialized.
        tdev=trig[city][(trig[city].index>='2023-01-01')&(trig[city].index<'2025-01-01')];daily=[]
        for dt,q in tdev.iterrows():
            p,ph=route_trigger(sr,st,q.T_rain,q.T_tide,hrv,htv,h0);th=thresholds[city]
            daily.append({'date':dt,'model_alert_all':float(np.mean(p>=th['all']['model']['medium'])),'hybrid_alert_all':float(np.mean(ph>=th['all']['hybrid']['medium'])),'model_alert_universe':float(np.mean(p[uni]>=th['universe']['model']['medium'])),'hybrid_alert_universe':float(np.mean(ph[uni]>=th['universe']['hybrid']['medium']))})
        ad=pd.DataFrame(daily);ad.to_parquet(root/'data/processed'/city/'daily_alert_index_dev.parquet',index=False);alerts[city]=len(ad)
    Path('models/combination_thresholds.json').write_text(json.dumps({'max_fit_date':'2022-12-31','thresholds':thresholds},indent=2))
    return {'best':_best_scorer(),'cities':{c:{'routes':len(v[0]),'in_universe':int(v[4].sum()),'fit_event_days':len(event_dates[c]),'h0':h0meta[c]['h0'],'dev_alert_days':alerts[c]} for c,v in scores.items()},'h0':h0meta,'thresholds':thresholds}

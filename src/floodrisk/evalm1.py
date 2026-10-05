"""Frozen, label-safe evaluation harness for route susceptibility Model 1."""
from __future__ import annotations
import hashlib, importlib.util, json, math, os, time, sys
from pathlib import Path
import resource
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import CRS

SEED=41073; BOOTSTRAPS=1000; CITY_ORDER=('ho_chi_minh','da_nang')
FORBIDDEN={'route_id','geometry','name','name_norm','ward_id','district_id','lat','lon','x','y','block_id','fold','city','highway_class'}
CLASS_GROUPS={'major':{'motorway','trunk','primary','secondary','motorway_link','trunk_link','primary_link','secondary_link'},'mid':{'tertiary','tertiary_link'},'minor':{'residential','unclassified','living_street'}}

def validate_scorer_frame(frame):
    bad=FORBIDDEN.intersection(frame.columns)
    if bad: raise ValueError(f'forbidden scorer columns: {sorted(bad)}')

def class_groups(highway):
    h=pd.Series(highway).astype(str).to_numpy(); out=np.full(len(h),'other',dtype=object)
    for g,values in CLASS_GROUPS.items():out[np.isin(h,list(values))]=g
    return out

def _binned_metrics(y, score, groups, builtup, positive_variant=None):
    y=np.asarray(y,dtype=bool);score=np.asarray(score,dtype=float);groups=np.asarray(groups); n=len(y)
    score=np.nan_to_num(score,nan=-np.inf,posinf=np.finfo(float).max,neginf=-np.finfo(float).min)
    _,bins=np.unique(score,return_inverse=True);k=int(bins.max()+1) if n else 0
    pc=np.bincount(bins[y],minlength=k).astype(float);nc=np.bincount(bins[~y],minlength=k).astype(float)
    def calc(p,neg, fraction=.1):
        P=p.sum();N=neg.sum()
        if P<=0 or N<=0:return {'recall':np.nan,'auc':np.nan,'ap':np.nan,'lift':np.nan}
        order=np.arange(len(p)-1,-1,-1);pr=p[order];nr=neg[order];total=(P+N);take=fraction*total
        cum=np.cumsum(pr+nr);prior=cum-(pr+nr);need=np.clip(take-prior,0,pr+nr);hit=np.divide(pr*need,pr+nr,out=np.zeros_like(pr),where=(pr+nr)>0).sum()/P
        # Grouped ties receive proportional selection at the top-k boundary.
        auc=float(np.dot(p,np.cumsum(neg)-neg+.5*neg)/(P*N))
        cp=np.cumsum(pr);cn=np.cumsum(nr);ap=float(np.sum((pr/P)*np.divide(cp,cp+cn,out=np.zeros_like(cp),where=(cp+cn)>0)))
        return {'recall':float(hit),'auc':auc,'ap':ap,'lift':float(hit/(P/total))}
    raw=calc(pc,nc)
    result={'recall_at_10':raw['recall'],'auc':raw['auc'],'average_precision':raw['ap'],'lift_at_10':raw['lift']}
    strat_hits=0.;strat_auc_num=0.;strat_auc_den=0.
    for group in ('major','mid','minor'):
        mask=groups==group; p=np.bincount(bins[mask&y],minlength=k).astype(float);neg=np.bincount(bins[mask&~y],minlength=k).astype(float)
        m=calc(p,neg);pos=p.sum();strat_hits+=m['recall']*pos if np.isfinite(m['recall']) else 0
        if np.isfinite(m['auc']):strat_auc_num+=m['auc']*pos;strat_auc_den+=pos
        result.update({f'{group}_{key}':val for key,val in m.items()})
    result['strat_recall_at_10']=strat_hits/max(1,y.sum())
    result['strat_auc']=strat_auc_num/strat_auc_den if strat_auc_den else np.nan
    if builtup is not None:
        b=np.asarray(builtup,dtype=float); terc=np.zeros(len(b),dtype=int); ok=np.isfinite(b)
        if ok.any(): terc[ok]=pd.qcut(pd.Series(b[ok]).rank(method='first'),q=3,labels=False,duplicates='drop').astype(int)
        g2=np.asarray([f'{g}:{t}' for g,t in zip(groups,terc)],dtype=object)
        hits=0.
        for group in np.unique(g2):
            mask=g2==group;p=np.bincount(bins[mask&y],minlength=k).astype(float);neg=np.bincount(bins[mask&~y],minlength=k).astype(float);m=calc(p,neg)
            if np.isfinite(m['recall']):hits+=m['recall']*p.sum()
        result['strat2_recall_at_10']=hits/max(1,y.sum())
    if positive_variant is not None:
        alt=np.asarray(positive_variant,dtype=bool);hits=0.
        for group in ('major','mid','minor'):
            mask=groups==group; p=np.bincount(bins[mask&alt],minlength=k).astype(float);neg=np.bincount(bins[mask&~alt],minlength=k).astype(float);m=calc(p,neg)
            if np.isfinite(m['recall']):hits+=m['recall']*p.sum()
        result['non_event_strat_recall_at_10']=hits/max(1,alt.sum())
    return result

def metric_values(y,scores,highway,builtup=None,positive_variant=None):
    return _binned_metrics(y,scores,class_groups(highway),builtup,positive_variant)

def bootstrap_metrics(y,scores,highway,builtup=None,positive_variant=None,draws=BOOTSTRAPS,seed=SEED):
    y=np.asarray(y,dtype=bool);scores=np.asarray(scores,dtype=float);groups=class_groups(highway);n=len(y)
    point=_binned_metrics(y,scores,groups,builtup,positive_variant)
    _,bins=np.unique(np.nan_to_num(scores,nan=-np.inf),return_inverse=True);k=int(bins.max()+1)
    pos=np.flatnonzero(y);neg=np.flatnonzero(~y);rng=np.random.default_rng(seed);vals={key:[] for key in point}
    group_codes=np.asarray([{'major':0,'mid':1,'minor':2}.get(g,-1) for g in groups]);
    bgroup=None
    if builtup is not None:
        b=np.asarray(builtup,dtype=float);terc=np.zeros(n,dtype=int);ok=np.isfinite(b)
        if ok.any():terc[ok]=pd.qcut(pd.Series(b[ok]).rank(method='first'),q=3,labels=False,duplicates='drop').astype(int)
        bgroup=group_codes*3+terc
    alt=np.asarray(positive_variant,dtype=bool) if positive_variant is not None else None
    def from_counts(p,nn):
        P=p.sum();N=nn.sum()
        if P<=0 or N<=0:return {'recall':np.nan,'auc':np.nan,'ap':np.nan,'lift':np.nan}
        po=np.cumsum(p[::-1]);no=np.cumsum(nn[::-1]);tot=po+no;take=.1*(P+N);prior=tot-(p[::-1]+nn[::-1]);bin_hits=np.minimum(p[::-1]+nn[::-1],np.maximum(0,take-prior));
        hit=float(np.sum(np.divide(p[::-1]*bin_hits,p[::-1]+nn[::-1],out=np.zeros_like(bin_hits),where=(p[::-1]+nn[::-1])>0))/P)
        auc=float(np.dot(p,np.cumsum(nn)-nn+.5*nn)/(P*N));ap=float(np.sum((p[::-1]/P)*np.divide(po,tot,out=np.zeros_like(po),where=tot>0)))
        return {'recall':hit,'auc':auc,'ap':ap,'lift':hit/ (P/(P+N))}
    for _ in range(draws):
        ix=np.r_[rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)];w=np.bincount(ix,minlength=n).astype(np.float32)
        p=np.bincount(bins,weights=w*y,minlength=k);nn=np.bincount(bins,weights=w*(~y),minlength=k);m=from_counts(p,nn)
        vals['recall_at_10'].append(m['recall']);vals['auc'].append(m['auc']);vals['average_precision'].append(m['ap']);vals['lift_at_10'].append(m['lift'])
        hits=0.;auc_num=0.;auc_den=0.
        for gi,g in enumerate(('major','mid','minor')):
            mask=group_codes==gi;pp=np.bincount(bins[mask],weights=w[mask]*y[mask],minlength=k);ng=np.bincount(bins[mask],weights=w[mask]*(~y[mask]),minlength=k);gm=from_counts(pp,ng);gp=pp.sum()
            hits+=gm['recall']*gp if np.isfinite(gm['recall']) else 0
            if np.isfinite(gm['auc']):auc_num+=gm['auc']*gp;auc_den+=gp
            for key,val in gm.items():vals[f'{g}_{key}'].append(val)
        vals['strat_recall_at_10'].append(hits/max(1,float(np.sum(w*y))));vals['strat_auc'].append(auc_num/auc_den if auc_den else np.nan)
        if bgroup is not None:
            h2=0.
            for gi in range(9):
                mask=bgroup==gi;pp=np.bincount(bins[mask],weights=w[mask]*y[mask],minlength=k);ng=np.bincount(bins[mask],weights=w[mask]*(~y[mask]),minlength=k);gm=from_counts(pp,ng)
                if np.isfinite(gm['recall']):h2+=gm['recall']*pp.sum()
            vals['strat2_recall_at_10'].append(h2/max(1,float(np.sum(w*y))))
        if alt is not None:
            ha=0.
            for gi in range(3):
                mask=group_codes==gi;pa=np.bincount(bins[mask],weights=w[mask]*alt[mask],minlength=k);nn_alt=np.bincount(bins[mask],weights=w[mask]*(~alt[mask]),minlength=k);gm=from_counts(pa,nn_alt)
                if np.isfinite(gm['recall']):ha+=gm['recall']*pa.sum()
            vals['non_event_strat_recall_at_10'].append(ha/max(1,float(np.sum(w*alt))))
    intervals={k:[float(np.nanquantile(v,.025)),float(np.nanquantile(v,.975))] if np.isfinite(v).any() else [np.nan,np.nan] for k,v in vals.items()}
    return point,intervals

def make_folds(city,routes,folds=5,seed=SEED):
    zone=48 if city=='ho_chi_minh' else 49
    geomframe=gpd.GeoDataFrame(routes,geometry='geometry',crs=4326) if not isinstance(routes,gpd.GeoDataFrame) else routes
    metric=geomframe.to_crs(CRS.from_epsg(32600+zone));cent=metric.geometry.representative_point()
    blockx=np.floor(cent.x.to_numpy()/2000).astype(int);blocky=np.floor(cent.y.to_numpy()/2000).astype(int)
    block=np.asarray([f'{x}:{y}' for x,y in zip(blockx,blocky)]);unique=np.unique(block);rng=np.random.default_rng(seed);rng.shuffle(unique)
    counts={b:int((block==b).sum()) for b in unique};loads=np.zeros(folds,dtype=int);assign={}
    for b in sorted(unique,key=lambda x:(-counts[x],int(hashlib.sha1(x.encode()).hexdigest()[:8],16))):
        f=int(np.argmin(loads));assign[b]=f;loads[f]+=counts[b]
    return np.asarray([assign[b] for b in block],dtype=int)

def load_data(city):
    root=Path('data/processed');features=pd.read_parquet(root/city/'route_features.parquet');routes=gpd.read_parquet(root/city/'routes.parquet',columns=['route_id','highway_class','geometry']);labels=pd.read_parquet(root/city/'route_labels.parquet')
    frame=features.loc[features.in_universe.astype(bool)].merge(routes[['route_id','highway_class','geometry']],on='route_id',how='inner',validate='one_to_one')
    if frame.route_id.duplicated().any():raise ValueError('duplicate route keys')
    frame=frame.merge(labels,on='route_id',how='left',validate='one_to_one',suffixes=('','_label'))
    frame['ever_flood_rain']=frame.ever_flood_rain.fillna(False).astype(bool);frame['ever_flood_tide']=frame.ever_flood_tide.fillna(False).astype(bool)
    # route_labels contain training splits only. first/last dates distinguish
    # routes with at least one non-2022-10-14 rain observation without opening
    # any raw flood-record rows (especially locked rows).
    first=pd.to_datetime(frame.first_date,errors='coerce').dt.date;last=pd.to_datetime(frame.last_date,errors='coerce').dt.date
    event_only=(first==pd.Timestamp('2022-10-14').date())&(last==pd.Timestamp('2022-10-14').date())
    frame['rain_non_event_positive']=frame.ever_flood_rain & ~event_only & (first.notna()|last.notna())
    return frame

def feature_manifest(city):
    raw=json.loads((Path('data/processed')/city/'feature_manifest.json').read_text())
    return {'feature_names':raw['feature_names'],'groups':raw['groups']}

def scorer_input(frame,target,include_label):
    cols=[c for c in frame.columns if c not in FORBIDDEN and c not in {'in_universe','ever_flood_rain','ever_flood_tide','rain_non_event_positive','n_records','n_distinct_dates','max_depth_cm','first_date','last_date','route_ways'}]
    x=frame[cols].copy().reset_index(drop=True)
    if include_label:
        y=frame[target].astype(int).to_numpy(); x['label']=y
        x['sample_weight']=np.where(frame.n_records.notna(),1.0,.2)
    validate_scorer_frame(x)
    return x

def _load_scorer(name):
    root=str(Path.cwd())
    if root not in sys.path:sys.path.insert(0,root)
    path=Path('experiments/m1')/(name+'.py');spec=importlib.util.spec_from_file_location('m1_'+name,path)
    if spec is None or spec.loader is None:raise FileNotFoundError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    if not callable(getattr(mod,'fit',None)) or not callable(getattr(mod,'predict',None)):raise TypeError(f'{name} must define fit and predict')
    return mod

def _score_fold(mod,train,test,city,target):
    tr=scorer_input(train,target,True);te=scorer_input(test,target,False)
    model=mod.fit(tr,feature_manifest(city),target)
    count=len(model['columns']) if isinstance(model,dict) and 'columns' in model else int(getattr(mod,'M1_FEATURE_COUNT',0))
    mod._eval_n_features=max(getattr(mod,'_eval_n_features',0),count)
    scores=np.asarray(mod.predict(model,te),dtype=float)
    if len(scores)!=len(test) or not np.isfinite(scores).all():raise ValueError(f'{mod.__name__}.predict returned invalid scores')
    return scores

def task_specs():return [('T1','ho_chi_minh','da_nang','ever_flood_rain','transfer'),('T2','da_nang','ho_chi_minh','ever_flood_rain','transfer'),('T3','ho_chi_minh','ho_chi_minh','ever_flood_tide','cv'),('T4','ho_chi_minh','ho_chi_minh','ever_flood_rain','cv'),('T5','da_nang','da_nang','ever_flood_rain','cv')]

def evaluate_scorer(name):
    mod=_load_scorer(name);results={};predictions={};t0=time.time()
    cache={c:load_data(c) for c in CITY_ORDER};folds={c:make_folds(c,cache[c]) for c in CITY_ORDER}
    for tid,train_city,test_city,target,mode in task_specs():
        tr=cache[train_city];te=cache[test_city]
        if mode=='transfer':
            score=_score_fold(mod,tr,te,train_city,target);pred=te.copy();pred['score']=score
        else:
            fold=folds[test_city];pred=te.copy();pred['score']=np.nan
            for f in range(5):
                testmask=fold==f;trainmask=~testmask
                pred.loc[testmask,'score']=_score_fold(mod,te.loc[trainmask],te.loc[testmask],train_city,target)
        y=pred[target].to_numpy(bool);alt=pred.rain_non_event_positive.to_numpy(bool) if tid=='T5' else None
        point,ci=bootstrap_metrics(y,pred.score.to_numpy(),pred.highway_class,pred.lc_builtup_500m_frac.to_numpy(),alt,seed=SEED+int(tid[1:]))
        results[tid]={'point':point,'ci':ci,'n':len(pred),'positives':int(y.sum())}
        predictions[tid]=pred[['route_id','score',target,'highway_class','lc_builtup_500m_frac']].copy()
    headline=float(np.mean([results[t]['point']['strat_recall_at_10'] for t in ('T1','T2','T3')]))
    headline2=float(np.mean([results[t]['point']['strat2_recall_at_10'] for t in ('T1','T2','T3')]))
    return {'scorer':name,'description':(mod.__doc__ or name).strip().splitlines()[0],'results':results,'HEADLINE':headline,'HEADLINE2':headline2,'runtime_seconds':time.time()-t0,'predictions':predictions,'module':mod,'n_features':getattr(mod,'_eval_n_features',0)}

def headline_bootstrap_difference(a,b,draws=BOOTSTRAPS,seed=SEED):
    rng=np.random.default_rng(seed);diffs=[]
    for task in ('T1','T2','T3'):
        pa=a['predictions'][task];pb=b['predictions'][task].set_index('route_id').loc[pa.route_id].reset_index()
        y=pa.iloc[:,2].to_numpy(bool);groups=class_groups(pa.highway_class);sa=pa.score.to_numpy();sb=pb.score.to_numpy();pos=np.flatnonzero(y);neg=np.flatnonzero(~y);n=len(y)
        _,ba=np.unique(sa,return_inverse=True);_,bb=np.unique(sb,return_inverse=True);ka=ba.max()+1;kb=bb.max()+1
        def strat_recall(bins,k,w):
            hits=0.;p_total=float(np.sum(w*y))
            for gi in ('major','mid','minor'):
                mask=groups==gi
                if not mask.any():continue
                pc=np.bincount(bins[mask],weights=w[mask]*y[mask],minlength=k);tc=np.bincount(bins[mask],weights=w[mask],minlength=k)
                cutoff=.1*tc.sum();ct=np.cumsum(tc[::-1]);before=ct-tc[::-1];take=np.clip(cutoff-before,0,tc[::-1])
                hits+=float(np.sum(np.divide(pc[::-1]*take,tc[::-1],out=np.zeros_like(take),where=tc[::-1]>0)))
            return hits/max(1.,p_total)
        ta=[];tb=[]
        for _ in range(draws):
            ix=np.r_[rng.choice(pos,len(pos),True),rng.choice(neg,len(neg),True)];w=np.bincount(ix,minlength=n).astype(np.float32)
            ta.append(strat_recall(ba,ka,w));tb.append(strat_recall(bb,kb,w))
        diffs.append(np.asarray(ta)-np.asarray(tb))
    x=np.mean(diffs,axis=0);return float(x.mean()),[float(np.quantile(x,.025)),float(np.quantile(x,.975))],float(np.mean(x>0))

def append_result(run,git_hash,peak_rss_mb,status='ok'):
    path=Path('reports/m1_results.tsv');path.parent.mkdir(parents=True,exist_ok=True)
    fields=['timestamp','git_short_hash','scorer','description','HEADLINE','HEADLINE2']
    for tid,*_ in task_specs():fields += [f'{tid}_strat_recall_at_10',f'{tid}_recall_at_10',f'{tid}_strat_auc',f'{tid}_auc']
    fields+=['runtime_seconds','peak_rss_mb','n_features','status']
    if not path.exists():path.write_text('\t'.join(fields)+'\n')
    vals=[pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').isoformat(),git_hash,run['scorer'],run['description'],f"{run['HEADLINE']:.8f}",f"{run['HEADLINE2']:.8f}"]
    for tid,*_ in task_specs():
        p=run['results'][tid]['point'];vals += [f"{p['strat_recall_at_10']:.8f}",f"{p['recall_at_10']:.8f}",f"{p['strat_auc']:.8f}",f"{p['auc']:.8f}"]
    vals += [f"{run['runtime_seconds']:.3f}",f'{peak_rss_mb:.2f}',str(run.get('n_features',0)),status]
    with path.open('a') as f:f.write('\t'.join(vals)+'\n')
    detail=Path('reports/m1_details.json');old=json.loads(detail.read_text()) if detail.exists() else {}
    old[run['scorer']]={'HEADLINE':run['HEADLINE'],'HEADLINE2':run['HEADLINE2'],'description':run['description'],'runtime_seconds':run['runtime_seconds'],'peak_rss_mb':peak_rss_mb,'n_features':run.get('n_features',0),'tasks':run['results']}
    detail.write_text(json.dumps(old,indent=2,allow_nan=True))

def run_importance(name,target='ever_flood_rain',city='ho_chi_minh'):
    """Aggregate gain importances from available fitted LightGBM baseline models."""
    mod=_load_scorer(name);data=load_data(city);x=scorer_input(data,target,True);model=mod.fit(x,feature_manifest(city),target)
    model=model.get('model') if isinstance(model,dict) else model
    if not hasattr(model,'booster_'):return []
    gains=model.booster_.feature_importance(importance_type='gain');names=model.booster_.feature_name()
    return sorted(zip(names,map(float,gains)),key=lambda z:z[1],reverse=True)[:15]

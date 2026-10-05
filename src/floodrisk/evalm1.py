"""Frozen, label-safe evaluation harness for route susceptibility Model 1."""
from __future__ import annotations
import hashlib, importlib.util, json, math, os, time, sys
from pathlib import Path
import resource
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import CRS
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import StratifiedKFold

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
    return point,intervals,vals

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
    root=Path('data/processed');paths=[root/city/'route_features.parquet',root/city/'routes.parquet',root/city/'route_labels.parquet']
    sig=hashlib.sha256('|'.join(f'{p.stat().st_size}:{p.stat().st_mtime_ns}' for p in paths).encode()).hexdigest()[:16]
    cp=root/'m1_cache';cp.mkdir(parents=True,exist_ok=True);cached=cp/f'frame_{city}_{sig}.pkl'
    if cached.exists():return pd.read_pickle(cached)
    features=pd.read_parquet(paths[0]);routes=gpd.read_parquet(paths[1],columns=['route_id','highway_class','geometry']);labels=pd.read_parquet(paths[2])
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
    frame.to_pickle(cached);return frame

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

EXPOSURE_NUM=['lanes','named','road_length_density_500m','road_intersections_300m','lc_builtup_200m_frac','lc_builtup_500m_frac','lc_tree_500m_frac','lc_grass_shrub_500m_frac','lc_cropland_500m_frac','lc_bare_500m_frac']
def exposure_scores(frame):
    """Cross-fitted reporting propensity, using only exposure covariates and observed-record presence."""
    d=frame.copy(); road='road_highway_rank' if 'road_highway_rank' in d else 'highway_class'
    num=[c for c in EXPOSURE_NUM if c in d]; x=d[num].apply(pd.to_numeric,errors='coerce')
    named='named' in x
    if named: x['named']=x['named'].astype(float)
    if road in d:x['__road']=d[road].astype(str)
    y=d.n_records.notna().astype(int).to_numpy() if 'n_records' in d else d.sample_weight.gt(.2).astype(int).to_numpy()
    if len(np.unique(y))<2:return np.full(len(d),float(y.mean() if len(y) else .5))
    cat=['__road'] if '__road' in x else [];nums=[c for c in x if c not in cat]
    prep=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()),nums),('cat',OneHotEncoder(handle_unknown='ignore'),cat)])
    out=np.zeros(len(d));folds=StratifiedKFold(n_splits=5,shuffle=True,random_state=SEED)
    for tr,te in folds.split(x,y):
        model=make_pipeline(prep,LogisticRegression(C=.5,max_iter=150,class_weight='balanced',random_state=SEED))
        model.fit(x.iloc[tr],y[tr]);out[te]=model.predict_proba(x.iloc[te])[:,1]
    return out

def _prop_metrics(y,score,prop,urban,draws=BOOTSTRAPS,seed=SEED):
    y=np.asarray(y,bool);score=np.asarray(score,float);prop=np.asarray(prop,float);n=len(y)
    strata=pd.qcut(pd.Series(prop).rank(method='first'),q=min(10,max(1,n)),labels=False,duplicates='drop').to_numpy()
    def calc(w=None):
        w=np.ones(n) if w is None else w
        pos_total=float(np.sum(w*y));hit=aucnum=aucden=0.
        for s in np.unique(strata):
            m=strata==s; pp=np.flatnonzero(m&y);nn=np.flatnonzero(m&~y)
            if not len(pp):continue
            take=max(1,int(np.ceil(.1*m.sum())))
            order=np.argsort(score[m])[::-1];ix=np.flatnonzero(m)[order[:take]]
            hit+=float(np.sum(w[ix]*y[ix]));
            if len(nn) and float(np.sum(w[m]*y[m]))>0 and float(np.sum(w[m]*(~y[m])))>0:
                from sklearn.metrics import roc_auc_score
                try:a=roc_auc_score(y[m],score[m],sample_weight=w[m]);aucnum+=a*float(np.sum(w[m]*y[m]));aucden+=float(np.sum(w[m]*y[m]))
                except ValueError:pass
        ur=np.flatnonzero(urban); uhit=0.
        if len(ur):
            ix=ur[np.argsort(score[ur])[::-1][:max(1,int(np.ceil(.1*len(ur))))]];up=float(np.sum(w[ur]*y[ur]));uhit=float(np.sum(w[ix]*y[ix]))/max(up,1.)
        return {'prop_recall_at_10':hit/max(pos_total,1.),'prop_auc':aucnum/aucden if aucden else np.nan,'urban_recall_at_10':uhit}
    point=calc();rng=np.random.default_rng(seed); vals={k:[] for k in point};p=np.flatnonzero(y);q=np.flatnonzero(~y)
    for _ in range(draws):
        ix=np.r_[rng.choice(p,len(p),True),rng.choice(q,len(q),True)] if len(p) and len(q) else np.arange(n)
        w=np.bincount(ix,minlength=n);z=calc(w)
        for k,v in z.items():vals[k].append(v)
    ci={k:[float(np.nanquantile(v,.025)),float(np.nanquantile(v,.975))] for k,v in vals.items()}
    return point,ci,vals

def evaluate_scorer(name,tasks=None,draws=BOOTSTRAPS):
    mod=_load_scorer(name);results={};predictions={};t0=time.time()
    cache={c:load_data(c) for c in CITY_ORDER};folds={c:make_folds(c,cache[c]) for c in CITY_ORDER}
    chosen=task_specs() if tasks is None else [x for x in task_specs() if x[0] in tasks]
    propcache={}
    for c in CITY_ORDER:
        cols=[z for z in EXPOSURE_NUM if z in cache[c]]+(['road_highway_rank'] if 'road_highway_rank' in cache[c] else [])+['n_records']
        sig=hashlib.sha256(pd.util.hash_pandas_object(cache[c][cols],index=False).values.tobytes()).hexdigest()[:16]
        cp=Path('data/processed/m1_cache');cp.mkdir(parents=True,exist_ok=True);path=cp/f'exposure_{c}_{sig}.npy'
        if path.exists():propcache[c]=np.load(path)
        else:propcache[c]=exposure_scores(cache[c]);np.save(path,propcache[c])
    joint={}
    for tid,train_city,test_city,target,mode in chosen:
        tr=cache[train_city];te=cache[test_city]
        if mode=='transfer':
            score=_score_fold(mod,tr,te,train_city,target);pred=te.copy();pred['score']=score
        else:
            fold=folds[test_city];pred=te.copy();pred['score']=np.nan
            for f in range(5):
                testmask=fold==f;trainmask=~testmask
                pred.loc[testmask,'score']=_score_fold(mod,te.loc[trainmask],te.loc[testmask],train_city,target)
        y=pred[target].to_numpy(bool);alt=pred.rain_non_event_positive.to_numpy(bool) if tid=='T5' else None
        point,ci,rep=bootstrap_metrics(y,pred.score.to_numpy(),pred.highway_class,pred.lc_builtup_500m_frac.to_numpy(),alt,draws=draws,seed=SEED+int(tid[1:]))
        ep,eci,erep=_prop_metrics(y,pred.score.to_numpy(),propcache[test_city],pred.lc_builtup_500m_frac.to_numpy()>=.5,draws,SEED+int(tid[1:]))
        point.update(ep);ci.update(eci);joint[tid]={'raw':rep,'prop':erep}
        results[tid]={'point':point,'ci':ci,'n':len(pred),'positives':int(y.sum())}
        predictions[tid]=pred[['route_id','score',target,'highway_class','lc_builtup_500m_frac']].copy();predictions[tid]['propensity']=propcache[test_city]
    primary=float(np.mean([results[t]['point']['prop_recall_at_10'] for t in ('T1','T2','T3') if t in results]))
    headline=float(np.mean([results[t]['point']['strat_recall_at_10'] for t in ('T1','T2','T3') if t in results]))
    headline2=float(np.mean([results[t]['point']['strat2_recall_at_10'] for t in ('T1','T2','T3') if t in results]))
    r=np.random.default_rng(SEED);m=min([len(joint[t]['prop']['prop_recall_at_10']) for t in ('T1','T2','T3') if t in joint])
    pri=np.mean([joint[t]['prop']['prop_recall_at_10'][:m] for t in ('T1','T2','T3') if t in joint],axis=0);hea=np.mean([joint[t]['raw']['strat_recall_at_10'][:m] for t in ('T1','T2','T3') if t in joint],axis=0)
    primary_ci=np.quantile(pri,[.025,.975]).tolist();headline_ci=np.quantile(hea,[.025,.975]).tolist()
    return {'scorer':name,'description':(mod.__doc__ or name).strip().splitlines()[0],'results':results,'PRIMARY':primary,'PRIMARY_ci':primary_ci,'HEADLINE':headline,'HEADLINE_ci':headline_ci,'HEADLINE2':headline2,'runtime_seconds':time.time()-t0,'predictions':predictions,'module':mod,'n_features':getattr(mod,'_eval_n_features',0)}

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

def append_result(run,git_hash,peak_rss_mb,status='ok',decision='baseline',vs_best=''):
    path=Path('reports/m1_results.tsv');path.parent.mkdir(parents=True,exist_ok=True)
    fields=['timestamp','git_short_hash','scorer','description','PRIMARY','PRIMARY_ci','HEADLINE','HEADLINE_ci','HEADLINE2']
    for tid,*_ in task_specs():fields += [f'{tid}_strat_recall_at_10',f'{tid}_recall_at_10',f'{tid}_strat_auc',f'{tid}_auc']
    fields+=['runtime_seconds','peak_rss_mb','n_features','status','decision','vs_best']
    if path.exists():
        old=pd.read_csv(path,sep='\t').fillna('')
        if 'PRIMARY' not in old.columns:
            for f in fields:
                if f not in old:old[f]='baseline' if f=='decision' else ''
            old=old[fields];old.to_csv(path,sep='\t',index=False)
    if not path.exists():path.write_text('\t'.join(fields)+'\n')
    vals=[pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').isoformat(),git_hash,run['scorer'],run['description'],f"{run['PRIMARY']:.8f}",str(run['PRIMARY_ci']),f"{run['HEADLINE']:.8f}",str(run['HEADLINE_ci']),f"{run['HEADLINE2']:.8f}"]
    for tid,*_ in task_specs():
        if tid not in run['results']:
            vals+=['']*4;continue
        p=run['results'][tid]['point'];vals += [f"{p['strat_recall_at_10']:.8f}",f"{p['recall_at_10']:.8f}",f"{p['strat_auc']:.8f}",f"{p['auc']:.8f}"]
    vals += [f"{run['runtime_seconds']:.3f}",f'{peak_rss_mb:.2f}',str(run.get('n_features',0)),status,decision,vs_best]
    with path.open('a') as f:f.write('\t'.join(vals)+'\n')
    detail=Path('reports/m1_details.json');old=json.loads(detail.read_text()) if detail.exists() else {}
    old[run['scorer']]={'PRIMARY':run['PRIMARY'],'PRIMARY_ci':run['PRIMARY_ci'],'HEADLINE':run['HEADLINE'],'HEADLINE_ci':run['HEADLINE_ci'],'HEADLINE2':run['HEADLINE2'],'description':run['description'],'runtime_seconds':run['runtime_seconds'],'peak_rss_mb':peak_rss_mb,'n_features':run.get('n_features',0),'tasks':run['results']}
    detail.write_text(json.dumps(old,indent=2,allow_nan=True))

def run_importance(name,target='ever_flood_rain',city='ho_chi_minh'):
    """Aggregate gain importances from available fitted LightGBM baseline models."""
    mod=_load_scorer(name);data=load_data(city);x=scorer_input(data,target,True);model=mod.fit(x,feature_manifest(city),target)
    model=model.get('model') if isinstance(model,dict) else model
    if not hasattr(model,'booster_'):return []
    gains=model.booster_.feature_importance(importance_type='gain');names=model.booster_.feature_name()
    return sorted(zip(names,map(float,gains)),key=lambda z:z[1],reverse=True)[:15]

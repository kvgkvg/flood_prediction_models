#!/usr/bin/env python3
"""Evaluate FIT-trained v2 route levels and rankings on 2023–2024 DEV."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from sklearn.metrics import roc_auc_score
from floodrisk.combine import route_bands,route_trigger

def boot_mean(values,seed=519,draws=2000):
    x=np.asarray(values,float);x=x[np.isfinite(x)]
    if not len(x):return np.nan,(np.nan,np.nan)
    rng=np.random.default_rng(seed);b=np.asarray([np.mean(x[rng.integers(0,len(x),len(x))]) for _ in range(draws)])
    return float(np.mean(x)),tuple(map(float,np.quantile(b,[.025,.975])))
def fmt(v):
    m,(lo,hi)=boot_mean(v)
    return f'{m:.3f} [{lo:.3f}, {hi:.3f}]' if np.isfinite(m) else 'NA'
def fmt_auc(v):
    m,(lo,hi)=v
    return f'{m:.3f} [{lo:.3f}, {hi:.3f}]' if np.isfinite(m) else 'NA'
def auc_ci(y,s,seed=719,draws=2000):
    y=np.asarray(y,bool);s=np.asarray(s,float)
    if not y.any() or y.all():return np.nan,(np.nan,np.nan)
    pos=np.flatnonzero(y);neg=np.flatnonzero(~y);rng=np.random.default_rng(seed);b=[]
    for _ in range(draws):
        ix=np.r_[rng.choice(pos,len(pos),True),rng.choice(neg,len(neg),True)]
        b.append(roc_auc_score(y[ix],s[ix]))
    return float(roc_auc_score(y,s)),tuple(map(float,np.quantile(b,[.025,.975])))
def _records():
    x=pd.read_parquet('data/processed/flood_records.parquet',columns=['record_id','city','date','cause','split'],filters=[('split','in',['train','train_undated'])])
    x['date']=pd.to_datetime(x.date,errors='coerce').dt.normalize()
    return x[(x.date>='2023-01-01')&(x.date<'2025-01-01')].copy()
def _matches(records):
    ids=records.record_id.astype(str).unique().tolist()
    d=ds.dataset('data/processed/flood_record_matches.parquet',format='parquet')
    x=d.to_table(columns=['record_id','route_id'],filter=ds.field('record_id').isin(ids)).to_pandas()
    x=x.dropna(subset=['route_id']);x.record_id=x.record_id.astype(str);x.route_id=x.route_id.astype(str)
    return records.merge(x,on='record_id',how='inner')
def _cause_level(band,t,threshold):
    if t>=threshold['t_hi']:return np.where(band==2,2,np.where(band==1,1,0)).astype(np.uint8)
    if t>=threshold['t_lo']:return np.where(band==2,1,0).astype(np.uint8)
    return np.zeros(len(band),np.uint8)
def _top(score,ids,k,tie=None):
    k=min(max(0,int(k)),len(ids))
    if k==0:return np.asarray([],int)
    sc=np.asarray(score)[ids];tie=sc if tie is None else np.asarray(tie)[ids]
    return ids[np.lexsort((-tie,-sc))[:k]]
def run(pilot=False):
    rec=_records();matched=_matches(rec)
    thresholds=json.loads(Path('models/combination_thresholds.json').read_text())['thresholds']
    results=[];cityinfo={}
    for city in ('ho_chi_minh','da_nang'):
        cols=['route_id','in_universe','S_rain','S_tide','S_hyb_rain','S_hyb_tide','H_rain','H_tide','H_any']
        path=Path('data/processed')/city/'route_susceptibility.parquet'
        if pilot:
            import pyarrow.parquet as pq
            ps=[]
            for b in pq.ParquetFile(path).iter_batches(batch_size=1000,columns=cols):
                ps.append(b.to_pandas())
                if sum(map(len,ps))>=5000:break
            s=pd.concat(ps,ignore_index=True).head(5000)
        else:s=pd.read_parquet(path,columns=cols)
        s.route_id=s.route_id.astype(str);ids=s.route_id.to_numpy();n=len(s);lookup={r:i for i,r in enumerate(ids)}
        uni=s.in_universe.to_numpy(bool);hist=s.H_any.to_numpy(bool);hr=s.H_rain.to_numpy(bool);ht=s.H_tide.to_numpy(bool)
        sr=s.S_rain.to_numpy(np.float32);st=s.S_tide.to_numpy(np.float32);shr=s.S_hyb_rain.to_numpy(np.float32);sht=s.S_hyb_tide.to_numpy(np.float32)
        assert np.all(shr>=sr) and np.all(sht>=st), 'hybrid S must preserve model S'
        model_score=np.maximum(sr,st);hybrid_score=np.maximum(shr,sht)
        masks={'all':np.ones(n,bool),'in_universe':uni};bands={}
        for scope,mask in masks.items():
            bands[scope]={'mr':route_bands(sr,sr,mask),'mt':route_bands(st,st,mask),'hr':route_bands(shr,sr,mask),'ht':route_bands(sht,st,mask)}
        d=rec[rec.city==city];m=matched[matched.city==city]
        byday={}
        for dt,g in m.groupby('date'):
            mp={}
            for rid,cause in zip(g.route_id.astype(str),g.cause.astype(str)):mp.setdefault(rid,set()).add(cause)
            byday[pd.Timestamp(dt)]=mp
        t=pd.read_parquet(Path('data/processed')/city/'trigger_daily.parquet');t.date=pd.to_datetime(t.date).dt.normalize();t=t.set_index('date')
        days=[x for x in pd.date_range('2023-01-01','2024-12-31',freq='D') if x in t.index]
        eventdays=set(d.date.dropna());rainseason=lambda z:(5<=z.month<=11) if city=='ho_chi_minh' else (9<=z.month<=12)
        hit={};budget={};burden={};d6={};alert_idx={scope:{x:[] for x in ('model','history','hybrid')} for scope in masks};alert_idx_new={scope:{x:[] for x in ('model','history','hybrid')} for scope in masks}
        for scope in masks:
            hit[scope]={x:[] for x in ('model','history','hybrid','new_model','new_history','new_hybrid')}
            budget[scope]={k:{x:[] for x in ('model','history','hybrid')} for k in ('history_count','5pct','20pct')}
            budget[scope]['new']={k:{x:[] for x in ('model','history','hybrid')} for k in ('history_count','5pct','20pct')}
            burden[scope]={q:{x:[] for x in ('model','history','hybrid','new_model','new_history','new_hybrid')} for q in ('flood','rain_no_report','dry')}
            d6[scope]={k:[] for k in ('5_hybrid','20_hybrid','5_new_hybrid','20_new_hybrid','5_model','20_model')}
        for day in days:
            q=t.loc[day];tr=float(q.T_rain);tt=float(q.T_tide);event=day in eventdays;mp=byday.get(day,{})
            pm=route_trigger(sr,st,tr,tt);ph=route_trigger(shr,sht,tr,tt)
            for scope,mask in masks.items():
                ix=np.flatnonzero(mask);b=bands[scope];th=thresholds[city]
                mlr=_cause_level(b['mr'],tr,th['rain']);mlt=_cause_level(b['mt'],tt,th['tide'])
                hlr=_cause_level(b['hr'],tr,th['rain']);hlt=_cause_level(b['ht'],tt,th['tide'])
                ml=np.maximum(mlr,mlt);hl=np.maximum(hlr,hlt);freshmask=mask&~hist
                alert_idx[scope]['model'].append(float(np.mean(ml[mask]>=1)))
                alert_idx[scope]['history'].append(float(np.mean(hist[mask])))
                alert_idx[scope]['hybrid'].append(float(np.mean(hl[mask]>=1)))
                if freshmask.any():
                    alert_idx_new[scope]['model'].append(float(np.mean(ml[freshmask]>=1)))
                    alert_idx_new[scope]['history'].append(0.)
                    alert_idx_new[scope]['hybrid'].append(float(np.mean(hl[freshmask]>=1)))
                positives=[]
                for rid,causes in mp.items():
                    if rid not in lookup or not mask[lookup[rid]]:continue
                    cs=[]
                    if 'rain' in causes or 'combined' in causes:cs.append('rain')
                    if 'tide' in causes or 'combined' in causes:cs.append('tide')
                    if not cs:cs=['rain','tide']
                    positives.append((lookup[rid],cs))
                if event and positives:
                    pv=[];hv=[];yv=[];fresh=[]
                    for j,cs in positives:
                        pv.append(any(mlr[j]>=1 if c=='rain' else mlt[j]>=1 for c in cs))
                        hv.append(any(hlr[j]>=1 if c=='rain' else hlt[j]>=1 for c in cs))
                        yv.append(any(hr[j] if c=='rain' else ht[j] for c in cs))
                        fresh.append(not hist[j])
                    fresh=np.asarray(fresh,bool)
                    for name,val in [('model',pv),('history',yv),('hybrid',hv)]:
                        hit[scope][name].append(float(np.mean(val)))
                        hit[scope]['new_'+name].append(float(np.mean(np.asarray(val)[fresh])) if fresh.any() else np.nan)
                    kh=int(hist[ix].sum());nscope=len(ix)
                    routeids=[ids[j] for j,_ in positives];newids=[r for r,z in zip(routeids,fresh) if z]
                    for key,k in [('history_count',kh),('5pct',max(1,int(np.ceil(.05*nscope)))),('20pct',max(1,int(np.ceil(.20*nscope))))]:
                        lists={'history':set(ids[ix[hist[ix]]]),'model':set(ids[_top(pm,ix,k)]),'hybrid':set(ids[_top(ph,ix,k)])}
                        for method,chosen in lists.items():
                            budget[scope][key][method].append(float(np.mean([r in chosen for r in routeids])))
                            budget[scope]['new'][key][method].append(float(np.mean([r in chosen for r in newids])) if newids else np.nan)
                    # D6 is record-weighted (duplicates on a route remain multiple records).
                    recday=m[m.date==day];rec_routes=recday.route_id.astype(str).tolist()
                    rec_new=[r for r in rec_routes if r in lookup and not hist[lookup[r]] and mask[lookup[r]]]
                    for pct,k in [('5',max(1,int(np.ceil(.05*nscope)))),('20',max(1,int(np.ceil(.20*nscope))))]:
                        for method,score in [('hybrid',hybrid_score),('model',model_score)]:
                            selected=set(ids[_top(score,ix,k,model_score)])
                            d6[scope][pct+'_'+method].append(float(np.mean([r in selected for r in rec_routes if r in lookup and mask[lookup[r]]])))
                            if method=='hybrid':d6[scope][pct+'_new_hybrid'].append(float(np.mean([r in selected for r in rec_new])) if rec_new else np.nan)
                typ='flood' if event else ('rain_no_report' if rainseason(day) else 'dry')
                for method,lv in [('model',ml),('hybrid',hl)]:
                    burden[scope][typ][method].append(float(np.mean(lv[mask]>=1)))
                    burden[scope][typ]['new_'+method].append(float(np.mean(lv[freshmask]>=1)) if freshmask.any() else np.nan)
                burden[scope][typ]['history'].append(float(np.mean(hist[mask])))
                burden[scope][typ]['new_history'].append(0. if freshmask.any() else np.nan)
        y=np.asarray([day in eventdays for day in days],bool)
        d4={}
        for scope in masks:
            for method in ('model','history','hybrid'):d4[(scope,method)]=auc_ci(y,alert_idx[scope][method])
        d4new={}
        for scope in masks:
            for method in ('model','history','hybrid'):d4new[(scope,method)]=auc_ci(y,alert_idx_new[scope][method])
        for scope in masks:
            for method in ('model','history','hybrid'):
                hitrow={'city':city,'scope':scope,'metric':'D1','method':method,'overall':fmt(hit[scope][method]),'new':fmt(hit[scope]['new_'+method])};results.append(hitrow)
            for key in ('history_count','5pct','20pct'):
                for method in ('model','history','hybrid'):
                    results.append({'city':city,'scope':scope,'metric':'D2_'+key,'method':method,'overall':fmt(budget[scope][key][method]),'new':fmt(budget[scope]['new'][key][method])})
            for typ in ('flood','rain_no_report','dry'):
                for method in ('model','history','hybrid'):
                    results.append({'city':city,'scope':scope,'metric':'D3_'+typ,'method':method,'overall':fmt(burden[scope][typ][method]),'new':fmt(burden[scope][typ]['new_'+method])})
            for pct in ('5','20'):
                for method in ('hybrid','model'):
                    key=pct+'_'+method
                    results.append({'city':city,'scope':scope,'metric':'D6_top'+pct,'method':method,'overall':fmt(d6[scope][key]),'new':fmt(d6[scope][pct+'_new_hybrid']) if method=='hybrid' else 'NA'})
            for method in ('model','history','hybrid'):
                results.append({'city':city,'scope':scope,'metric':'D4_alert_index_auc','method':method,'overall':fmt_auc(d4[(scope,method)]),'new':fmt_auc(d4new[(scope,method)])})
            for key in ('history_count','5pct','20pct'):
                results.append({'city':city,'scope':scope,'metric':'D2_hybrid_minus_history_'+key,'method':'paired delta','overall':fmt(np.asarray(budget[scope][key]['hybrid'])-np.asarray(budget[scope][key]['history'])),'new':'NA'})
                results.append({'city':city,'scope':scope,'metric':'D2_hybrid_minus_model_'+key,'method':'paired delta','overall':fmt(np.asarray(budget[scope][key]['hybrid'])-np.asarray(budget[scope][key]['model'])),'new':'NA'})
        cityinfo[city]={'records':len(d),'dates':d.date.nunique(),'matched_days':len(set(eventdays)&set(byday)),'unmatched':len(d)-d.record_id.isin(m.record_id).sum(),'d4':d4,'d4new':d4new}
    if pilot:
        print(f'DEV pilot passed: {len(results)} rows, no files written');return
    reports=['# Combination v2 DEV evaluation','','A1 diagnosis of v1 HCMC D1: FIT medium cutoffs differed by population (all routes 0.0449; in-universe 0.4033). The 44 matched in-universe DEV flood routes had max P=0.0709; none passed 0.4033, while 11 passed the lower all-route cutoff. The OOU group did not have higher P (1 matched DEV route, P=0; OOU route-day P p95=0). Driver shift compounded this: HCMC DEV positive-day max T_rain max=0.068 vs FIT positive max=0.153, and T_tide max=0.061 vs 0.911. V2 removes population-specific P quantile levels.','', 'Levels use per-cause FIT-only T states and route bands: A top 5%, B next 15%, C rest; high=alert+A, medium=alert+B or watch+A. Model-only uses S_model; hybrid uses S_hyb=max(S_model,S_hist); history-only flags FIT routes. P_model/P_hybrid remain continuous routing-cost scores. This is a documented change from the prior flood-day-P quantile rule because that rule produced a population-dependent zero-alert failure.','', 'Rainy-season no-report days are season days without a record of the cause. Unreported days are not confirmed dry. All DEV labels are 2023–2024; locked records were filtered out before attributes were read. Intervals bootstrap days.','']
    for city in ('ho_chi_minh','da_nang'):
        info=cityinfo[city];reports += [f"## {city}",'',f"DEV records={info['records']}; distinct report dates={info['dates']}; matched event days={info['matched_days']}; unmatched records={info['unmatched']}.",'', '| Scope | D1 Model | D1 History | D1 Hybrid | D1 NEW Model | D1 NEW History | D1 NEW Hybrid |','|---|---:|---:|---:|---:|---:|---:|']
        for scope in ('all','in_universe'):
            rr=[z for z in results if z['city']==city and z['scope']==scope and z['metric']=='D1']
            reports.append('| '+scope+' | '+' | '.join(next(z['overall'] for z in rr if z['method']==m) for m in ('model','history','hybrid'))+' | '+' | '.join(next(z['new'] for z in rr if z['method']==m) for m in ('model','history','hybrid'))+' |')
        reports += ['', 'D2 equal route-budget hit rate (K=history-list size / 5% / 20%); each cell is the ordered three-budget vector with day-bootstrap 95% CI. NEW restricts denominators to DEV routes without FIT history.','', '| Scope | Method | Overall | NEW |','|---|---|---:|---:|']
        for scope in ('all','in_universe'):
            for method in ('history','model','hybrid'):
                rr=[z for z in results if z['city']==city and z['scope']==scope and z['metric'].startswith('D2_') and z['method']==method]
                overall=' / '.join(next(z['overall'] for z in rr if z['metric']=='D2_'+k) for k in ('history_count','5pct','20pct'))
                new=' / '.join(next(z['new'] for z in rr if z['metric']=='D2_'+k) for k in ('history_count','5pct','20pct'))
                reports.append(f'| {scope} | {method} | {overall} | {new} |')
        reports += ['', 'D2 paired hybrid dominance check: hybrid S is pointwise >= both component scores by construction. The table reports paired hit-rate difference hybrid minus each comparator at K=history size/5%/20%; positive is better, and its 95% day-bootstrap CI shows whether the empirical top-K property holds.','', '| Scope | Comparator | Delta Khist / 5% / 20% |','|---|---|---:|']
        for scope in ('all','in_universe'):
            for comp in ('history','model'):
                keys=['D2_hybrid_minus_'+comp+'_'+k for k in ('history_count','5pct','20pct')]
                vals=[next(z['overall'] for z in results if z['city']==city and z['scope']==scope and z['metric']==key) for key in keys]
                reports.append(f'| {scope} | {comp} | '+' / '.join(vals)+' |')
        reports += ['', 'D3 alert burden: share of routes at medium/high on DEV record days / rainy-season no-report days / dry-season days. Values include point estimates and 95% day-bootstrap intervals; NEW restricts routes to no FIT history.','', '| Scope | Method | Overall | NEW |','|---|---|---:|---:|']
        for scope in ('all','in_universe'):
            for method in ('history','model','hybrid'):
                rr=[z for z in results if z['city']==city and z['scope']==scope and z['metric'].startswith('D3_') and z['method']==method]
                overall=' / '.join(next(z['overall'] for z in rr if z['metric']=='D3_'+k) for k in ('flood','rain_no_report','dry'))
                new=' / '.join(next(z['new'] for z in rr if z['metric']=='D3_'+k) for k in ('flood','rain_no_report','dry'))
                reports.append(f'| {scope} | {method} | {overall} | {new} |')
        for scope in ('all','in_universe'):
            vals={method:info['d4'][(scope,method)] for method in ('model','history','hybrid')}
            reports += ['',f"D4 {scope} city alert-index AUC: "+'; '.join(f"{m} {v[0]:.3f} [{v[1][0]:.3f}, {v[1][1]:.3f}]" for m,v in vals.items())+'.']
            valsnew={method:info['d4new'][(scope,method)] for method in ('model','history','hybrid')}
            reports.append(f"D4 {scope} NEW-route alert-index AUC: "+'; '.join(f"{m} {v[0]:.3f} [{v[1][0]:.3f}, {v[1][1]:.3f}]" for m,v in valsnew.items())+'.')
        reports += ['', 'D6: share of matched DEV flood-day records with route in top 5% / 20% by S_hyb, independent of T (all / NEW):','', '| Scope | All records, top5 / top20 | NEW records, top5 / top20 |','|---|---:|---:|']
        for scope in ('all','in_universe'):
            vals=[]
            for pct in ('5','20'):
                vals.append(next(z['overall'] for z in results if z['city']==city and z['scope']==scope and z['metric']=='D6_top'+pct and z['method']=='hybrid'))
            news=[]
            for pct in ('5','20'):
                news.append(next(z['new'] for z in results if z['city']==city and z['scope']==scope and z['metric']=='D6_top'+pct and z['method']=='hybrid'))
            reports.append(f'| {scope} | {vals[0]} / {vals[1]} | {news[0]} / {news[1]} |')
        reports.append('')
    if pilot:print(f'DEV pilot passed: {len(results)} rows; no reports written');return
    Path('reports/dev_eval.md').write_text('\n'.join(reports)+'\n')
    pd.DataFrame(results).to_csv('reports/dev_results.tsv',sep='\t',index=False)
    print(f'wrote reports/dev_eval.md and reports/dev_results.tsv ({len(results)} metric rows)')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');run(p.parse_args().pilot)

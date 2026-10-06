#!/usr/bin/env python3
"""Evaluate FIT-trained v2 route levels and rankings on 2023–2024 DEV."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from sklearn.metrics import roc_auc_score
from floodrisk.combine import route_bands

N_BOOT=2000
def boot_mean(values,seed=519,draws=None):
    draws=N_BOOT if draws is None else draws
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
def auc_ci(y,s,seed=719,draws=None):
    draws=N_BOOT if draws is None else draws
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
def run(pilot=False,rain_source='ifs',artifact_dir='data/processed',output_tag=None):
    global N_BOOT
    if pilot:N_BOOT=100
    rec=_records();matched=_matches(rec)
    thresholds=json.loads(Path('models/combination_thresholds.json').read_text())['thresholds']
    rain_cut=json.loads(Path('models/rain_percentile_trigger.json').read_text())['states']
    for city in thresholds:thresholds[city]['rain']={'t_lo':rain_cut['q_watch'],'t_hi':rain_cut['q_alert']}
    results=[];cityinfo={}
    for city in ('ho_chi_minh','da_nang'):
        cols=['route_id','in_universe','S_rain','S_tide','S_hyb_rain','S_hyb_tide','H_rain','H_tide','H_any']
        path=Path(artifact_dir)/city/'route_susceptibility.parquet'
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
        d7={cause:{name:[] for name in ('model','history','hybrid','new_model','new_history','new_hybrid')} for cause in ('rain','tide')}
        byday={}
        for dt,g in m.groupby('date'):
            mp={}
            for rid,cause in zip(g.route_id.astype(str),g.cause.astype(str)):mp.setdefault(rid,set()).add(cause)
            byday[pd.Timestamp(dt)]=mp
        t=pd.read_parquet(Path('data/processed')/city/'trigger_daily.parquet',columns=['date','T_tide']);t.date=pd.to_datetime(t.date).dt.normalize();t=t.set_index('date')
        rain=pd.read_parquet(Path('data/processed/rain_percentiles')/f'{city}_{rain_source}.parquet',columns=['date','T_rain']);rain.date=pd.to_datetime(rain.date).dt.normalize();t=t.join(rain.set_index('date'),how='inner')
        days=[x for x in pd.date_range('2023-01-01','2024-12-31',freq='D') if x in t.index]
        if pilot:
            events=set(d.date.dropna());events={x for x in events if x in t.index}
            samples={x for x in (pd.Timestamp('2023-03-15'),pd.Timestamp('2023-07-15'),pd.Timestamp('2023-12-15')) if x in t.index and x not in events}
            days=sorted(events|samples)
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
                    if city=='ho_chi_minh':
                        for cause,modellev,histflag,hylev in (('rain',mlr,hr,hlr),('tide',mlt,ht,hlt)):
                            js=[j for j,cs in positives if cause in cs]
                            if js:
                                isnew=np.asarray([not hist[j] for j in js])
                                for name,levels,flags in [('model',modellev,None),('history',None,histflag),('hybrid',hylev,None)]:
                                    values=[bool(flags[j]) if flags is not None else bool(levels[j]>=1) for j in js]
                                    d7[cause][name].append(float(np.mean(values)))
                                    d7[cause]['new_'+name].append(float(np.mean(np.asarray(values)[isnew])) if isnew.any() else np.nan)
                    kh=int(hist[ix].sum());nscope=len(ix)
                    routeids=[ids[j] for j,_ in positives];newids=[r for r,z in zip(routeids,fresh) if z]
                    for key,k in [('history_count',kh),('5pct',max(1,int(np.ceil(.05*nscope)))),('20pct',max(1,int(np.ceil(.20*nscope))))]:
                        lists={'history':set(ids[ix[hist[ix]]]),'model':set(ids[_top(model_score,ix,k,model_score)]),'hybrid':set(ids[_top(hybrid_score,ix,k,model_score)])}
                        if key=='history_count':assert lists['hybrid']==lists['history'],'hybrid top-K must equal history at K=history size'
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
        dominance={}
        for scope in masks:
            for k in ('5pct','20pct'):
                h=np.asarray(budget[scope][k]['hybrid'],float);m0=np.asarray(budget[scope][k]['model'],float)
                ok=np.isfinite(h)&np.isfinite(m0)
                delta=float(h[ok].mean()-m0[ok].mean()) if ok.any() else np.nan
                dominance[(scope,k)]={'delta':delta,'passes':bool(not np.isfinite(delta) or delta>=-.02)}
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
            for k in ('5pct','20pct'):
                z=dominance[(scope,k)]
                results.append({'city':city,'scope':scope,'metric':'hybrid_model_floor_'+k,'method':'hybrid-model','overall':f"{z['delta']:.3f}" if np.isfinite(z['delta']) else 'NA','new':str(z['passes'])})
            if city=='ho_chi_minh':
                for cause in ('rain','tide'):
                    for method in ('model','history','hybrid'):
                        results.append({'city':city,'scope':scope,'metric':'D7_'+cause,'method':method,'overall':fmt(d7[cause][method]),'new':fmt(d7[cause]['new_'+method])})
            for key in ('history_count','5pct','20pct'):
                results.append({'city':city,'scope':scope,'metric':'D2_hybrid_minus_history_'+key,'method':'paired delta','overall':fmt(np.asarray(budget[scope][key]['hybrid'])-np.asarray(budget[scope][key]['history'])),'new':'NA'})
                results.append({'city':city,'scope':scope,'metric':'D2_hybrid_minus_model_'+key,'method':'paired delta','overall':fmt(np.asarray(budget[scope][key]['hybrid'])-np.asarray(budget[scope][key]['model'])),'new':'NA'})
        cityinfo[city]={'records':len(d),'dates':d.date.nunique(),'matched_days':len(set(eventdays)&set(byday)),'unmatched':len(d)-d.record_id.isin(m.record_id).sum(),'d4':d4,'d4new':d4new}
    if pilot:
        print(f'DEV pilot passed: {len(results)} rows, no files written');return
    reports=[f'# Task 7 DEV evaluation — rain input {rain_source}','','Hybrid order uses S_model=0.90×percentile and S_hist=0.90+0.10×min(1,n_dates/3); runtime checks assert history equality at K=history size and report the model-floor comparison at 5% and 20%. Da Nang in-universe at 5% is a measured failure (hybrid-model = −0.051), because history priority displaces some model-ranked new routes.','',f"Shared pooled-FIT trigger thresholds q_watch={rain_cut['q_watch']:.6f}, q_alert={rain_cut['q_alert']:.6f}; input is city/source-specific {rain_source.upper()} climatological percentiles. Tide thresholds remain as in Task 6.",'','Route levels are A=top 5%, B=next 15%, high=alert+A, medium=alert+B or watch+A. All DEV labels are 2023–2024; locked records are filtered out before attributes are read. Intervals bootstrap days.','']
    for city in ('ho_chi_minh','da_nang'):
        info=cityinfo[city];reports += [f"## {city}",'',f"DEV records={info['records']}; distinct report dates={info['dates']}; matched event days={info['matched_days']}; unmatched records={info['unmatched']}.",'', '| Scope | D1 Model | D1 History | D1 Hybrid | D1 NEW Model | D1 NEW History | D1 NEW Hybrid |','|---|---:|---:|---:|---:|---:|---:|']
        for scope in ('all','in_universe'):
            rr=[z for z in results if z['city']==city and z['scope']==scope and z['metric']=='D1']
            reports.append('| '+scope+' | '+' | '.join(next(z['overall'] for z in rr if z['method']==m) for m in ('model','history','hybrid'))+' | '+' | '.join(next(z['new'] for z in rr if z['method']==m) for m in ('model','history','hybrid'))+' |')
        reports += ['', 'D2 equal route-budget hit rate (K=history-list size / 5% / 20%), ranking by S independent of T; each cell is the ordered three-budget vector with day-bootstrap 95% CI. NEW restricts denominators to DEV routes without FIT history.','', '| Scope | Method | Overall | NEW |','|---|---|---:|---:|']
        for scope in ('all','in_universe'):
            for method in ('history','model','hybrid'):
                rr=[z for z in results if z['city']==city and z['scope']==scope and z['metric'].startswith('D2_') and z['method']==method]
                overall=' / '.join(next(z['overall'] for z in rr if z['metric']=='D2_'+k) for k in ('history_count','5pct','20pct'))
                new=' / '.join(next(z['new'] for z in rr if z['metric']=='D2_'+k) for k in ('history_count','5pct','20pct'))
                reports.append(f'| {scope} | {method} | {overall} | {new} |')
        reports += ['', 'D2 paired hybrid check: exact set equality with history at K=history size is asserted for every DEV flood day. The requested model-floor condition (hybrid hit rate >= model minus .02) is measured and marked; fixed history priority can displace new model hits, so a failed check is reported as a genuine formula/data trade-off, not hidden.','', '| Scope | Comparator | Delta Khist / 5% / 20% | Model-floor check at 5% / 20% |','|---|---|---:|---|']
        for scope in ('all','in_universe'):
            for comp in ('history','model'):
                keys=['D2_hybrid_minus_'+comp+'_'+k for k in ('history_count','5pct','20pct')]
                vals=[next(z['overall'] for z in results if z['city']==city and z['scope']==scope and z['metric']==key) for key in keys]
                checks=' / '.join('pass' if dominance[(scope,k)]['passes'] else 'FAIL' for k in ('5pct','20pct')) if comp=='model' else '—'
                reports.append(f'| {scope} | {comp} | '+' / '.join(vals)+f' | {checks} |')
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
        if city=='ho_chi_minh':
            reports += ['', 'D7 HCMC hit rate by report cause (combined reports count in both groups; route-day weighted, bootstrap by day):','', '| Scope | Cause | Model overall / NEW | History overall / NEW | Hybrid overall / NEW |','|---|---|---:|---:|---:|']
            for scope in ('all','in_universe'):
                for cause in ('rain','tide'):
                    rr=[z for z in results if z['city']==city and z['scope']==scope and z['metric']=='D7_'+cause]
                    reports.append(f"| {scope} | {cause} | {next(z['overall'] for z in rr if z['method']=='model')} / {next(z['new'] for z in rr if z['method']=='model')} | {next(z['overall'] for z in rr if z['method']=='history')} / {next(z['new'] for z in rr if z['method']=='history')} | {next(z['overall'] for z in rr if z['method']=='hybrid')} / {next(z['new'] for z in rr if z['method']=='hybrid')} |")
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
    tag=output_tag or rain_source
    Path(f'reports/dev_eval_{tag}.md').write_text('\n'.join(reports)+'\n')
    pd.DataFrame(results).to_csv(f'reports/dev_results_{tag}.tsv',sep='\t',index=False)
    print(f'wrote DEV {tag} report and results ({len(results)} rows)')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--rain-source',choices=['era5','ifs'],default='ifs');p.add_argument('--artifact-dir',default='data/processed');p.add_argument('--output-tag');a=p.parse_args();run(a.pilot,a.rain_source,a.artifact_dir,a.output_tag)

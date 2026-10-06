#!/usr/bin/env python3
"""Evaluate FIT-trained route alerts on 2023–2024 only, one day at a time."""
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from sklearn.metrics import roc_auc_score
from floodrisk.combine import route_trigger
from floodrisk.combine import read_fit_records

ROOT=Path('.')
def boot_mean(values,seed=519,draws=2000):
    x=np.asarray(values,float);x=x[np.isfinite(x)]
    if not len(x):return np.nan,(np.nan,np.nan)
    rng=np.random.default_rng(seed);b=np.asarray([np.mean(x[rng.integers(0,len(x),len(x))]) for _ in range(draws)])
    return float(np.mean(x)),tuple(map(float,np.quantile(b,[.025,.975])))

def ci_text(values):
    m,(lo,hi)=boot_mean(values)
    return f'{m:.3f} [{lo:.3f}, {hi:.3f}]' if np.isfinite(m) else 'NA'

def _records():
    # Predicate pushdown: the locked rows are not read into this process.
    x=pd.read_parquet(ROOT/'data/processed/flood_records.parquet',columns=['record_id','city','date','cause','split'],filters=[('split','in',['train','train_undated'])])
    x['date']=pd.to_datetime(x.date,errors='coerce').dt.normalize()
    return x[(x.date>='2023-01-01')&(x.date<'2025-01-01')].copy()

def _matches(records):
    ids=records.record_id.astype(str).unique().tolist();d=ds.dataset(ROOT/'data/processed/flood_record_matches.parquet',format='parquet')
    x=d.to_table(columns=['record_id','route_id'],filter=ds.field('record_id').isin(ids)).to_pandas()
    x=x.dropna(subset=['route_id']);x.record_id=x.record_id.astype(str);x.route_id=x.route_id.astype(str)
    return records.merge(x,on='record_id',how='inner')

def _boot_auc(y,s,seed=719,draws=2000):
    y=np.asarray(y,bool);s=np.asarray(s,float)
    if not y.any() or y.all():return np.nan,(np.nan,np.nan)
    point=float(roc_auc_score(y,s));pos=np.flatnonzero(y);neg=np.flatnonzero(~y);rng=np.random.default_rng(seed);b=[]
    for _ in range(draws):
        ix=np.r_[rng.choice(pos,len(pos),True),rng.choice(neg,len(neg),True)]
        b.append(roc_auc_score(y[ix],s[ix]))
    return point,tuple(map(float,np.quantile(b,[.025,.975])))

def run():
    rec=_records();matched=_matches(rec);outputs=[];lines=['# Model 2/combination DEV rehearsal','','All DEV summaries use dated unlocked records from 2023–2024; 2025+ records were predicate-filtered out before attributes were read. Intervals resample flood days. Route-day risk is computed in a per-day loop; no route × calendar-day matrix is constructed. A hit means a matched DEV flood route is selected. Unmatched reports are excluded from route hit rates and counted below.','']
    all_city_summary=[]
    for city in ('ho_chi_minh','da_nang'):
        s=pd.read_parquet(ROOT/'data/processed'/city/'route_susceptibility.parquet')
        s.route_id=s.route_id.astype(str);routes=pd.read_parquet(ROOT/'data/processed'/city/'routes.parquet',columns=['route_id','highway_class']);routes.route_id=routes.route_id.astype(str)
        s=s.merge(routes,on='route_id',how='left',suffixes=('','_route'))
        uni=s.in_universe.astype(bool).to_numpy();ids=s.route_id.to_numpy();idix={v:i for i,v in enumerate(ids)}
        d=rec[rec.city==city];m=matched[matched.city==city];bydate={pd.Timestamp(k):set(g.route_id.astype(str)) for k,g in m.groupby('date')}
        ad=pd.read_parquet(ROOT/'data/processed'/city/'daily_alert_index_dev.parquet');ad.date=pd.to_datetime(ad.date).dt.normalize();ad=ad.set_index('date')
        t=pd.read_parquet(ROOT/'data/processed'/city/'trigger_daily.parquet');t.date=pd.to_datetime(t.date).dt.normalize();t=t.set_index('date')
        import json
        h0=float(json.loads((ROOT/'models/m2_history_h0.json').read_text())['selection'][city]['h0'])
        th=json.loads((ROOT/'models/combination_thresholds.json').read_text())['thresholds'][city]
        H=s.H_any.to_numpy(np.float32);hr=s.H_rain.to_numpy(np.float32);ht=s.H_tide.to_numpy(np.float32)
        event_days=sorted(set(d.date.dropna()))
        day_cache={}
        for dt in pd.date_range('2023-01-01','2024-12-31',freq='D'):
            if dt not in t.index:continue
            q=t.loc[dt];p,ph=route_trigger(s.S_rain.to_numpy(np.float32),s.S_tide.to_numpy(np.float32),q.T_rain,q.T_tide,hr,ht,h0)
            day_cache[dt]=(p,ph)
        subsets={'all':np.ones(len(s),bool),'in_universe':uni}
        cityres=[]
        for scope,mask in subsets.items():
            idx=np.flatnonzero(mask);n=len(idx);hist=H.astype(bool)&mask
            model_hits=[];hist_hits=[];hyb_hits=[];newhits={x:[] for x in ('model','history','hybrid')}
            budget_values={k:{x:[] for x in ('history','model','hybrid')} for k in ('history_count','5pct','20pct')}
            new_budget_values={k:{x:[] for x in ('history','model','hybrid')} for k in ('history_count','5pct','20pct')}
            alert={'flood':{'model':[],'history':[],'hybrid':[]},'rain_no_record':{'model':[],'history':[],'hybrid':[]},'dry_no_record':{'model':[],'history':[],'hybrid':[]}}
            for dt,(p,ph) in day_cache.items():
                pos=bydate.get(dt,set());pix=np.asarray([idix[x] for x in pos if x in idix and mask[idix[x]]],int)
                is_event=dt in event_days
                if is_event and len(pix):
                    pmask=p>=th[scope]['model']['medium'];hymask=ph>=th[scope]['hybrid']['medium'];hmask=hist
                    model_hits.append(float(pmask[pix].mean()));hist_hits.append(float(hmask[pix].mean()));hyb_hits.append(float(hymask[pix].mean()))
                    fresh=np.asarray([j for j in pix if not hist[j]],int)
                    if len(fresh):
                        newhits['model'].append(float(pmask[fresh].mean()));newhits['history'].append(0.);newhits['hybrid'].append(float(hymask[fresh].mean()))
                    k_hist=int(hmask.sum())
                    for key,k in [('history_count',k_hist),('5pct',max(1,int(np.ceil(.05*n)))),('20pct',max(1,int(np.ceil(.20*n))))]:
                        for label,score in [('history',H),('model',p),('hybrid',ph)]:
                            order=np.argsort(score[idx],kind='stable')[::-1][:min(k,n)];chosen=idx[order]
                            if key=='history_count' and label=='history':chosen=idx[hmask[idx]]
                            budget_values[key][label].append(float(np.isin(pix,chosen).mean()))
                            if len(fresh):new_budget_values[key][label].append(0. if label=='history' else float(np.isin(fresh,chosen).mean()))
                # Alert burden, using same medium threshold as route presentation.
                recday=dt in event_days
                month=dt.month;season=5<=month<=11 if city=='ho_chi_minh' else 9<=month<=12
                typ='flood' if recday else ('rain_no_record' if season else 'dry_no_record')
                alert[typ]['model'].append(float(np.mean(p[mask]>=th[scope]['model']['medium'])) if n else np.nan)
                alert[typ]['history'].append(float(np.mean(hist[mask])) if n else np.nan)
                alert[typ]['hybrid'].append(float(np.mean(ph[mask]>=th[scope]['hybrid']['medium'])) if n else np.nan)
            row={'city':city,'scope':scope,'flood_days_with_matched_routes':len(model_hits),'model_D1':ci_text(model_hits),'history_D1':ci_text(hist_hits),'hybrid_D1':ci_text(hyb_hits),'new_days':len(newhits['model']),'model_new_D1':ci_text(newhits['model']),'history_new_D1':ci_text(newhits['history']),'hybrid_new_D1':ci_text(newhits['hybrid'])}
            for budget,vs in budget_values.items():
                for method,vals in vs.items():row[f'{budget}_{method}']=ci_text(vals)
            for budget,vs in new_budget_values.items():
                for method,vals in vs.items():row[f'new_{budget}_{method}']=ci_text(vals)
            for typ,vs in alert.items():
                for method,vals in vs.items():row[f'{typ}_{method}']=ci_text(vals)
            yy=np.asarray([dt in event_days for dt in day_cache]);alert_index=np.asarray([ad.loc[dt,'model_alert_'+('universe' if scope=='in_universe' else 'all')] for dt in day_cache if dt in ad.index])
            if len(alert_index)==len(yy):
                auc,auc_ci=_boot_auc(yy,alert_index)
            else:auc,auc_ci=np.nan,(np.nan,np.nan)
            row['D4_model_alert_auc']=f'{auc:.3f} [{auc_ci[0]:.3f}, {auc_ci[1]:.3f}]' if np.isfinite(auc) else 'NA'
            row['dev_records']=int(len(d));row['dev_distinct_dates']=int(d.date.nunique());row['unmatched_records']=int(len(d)-d.record_id.isin(m.record_id).sum())
            cityres.append(row);outputs.append(row)
        lines += [f'## {city}', '', f"DEV records: {len(d)} on {d.date.nunique()} distinct dates; flood days with any dated record: {len(event_days)}; records unmatched to routes: {len(d)-d.record_id.isin(m.record_id).sum()}.", '', '| Scope | days | D1 P | D1 history | D1 hybrid | NEW P | NEW history | NEW hybrid | D4 AUC |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for r in cityres:lines.append(f"| {r['scope']} | {r['flood_days_with_matched_routes']} | {r['model_D1']} | {r['history_D1']} | {r['hybrid_D1']} | {r['model_new_D1']} | {r['history_new_D1']} | {r['hybrid_new_D1']} | {r['D4_model_alert_auc']} |")
        lines += ['', 'Equal route budget hit rate (mean [95% flood-day bootstrap CI]):', '', '| Scope / budget | History | Model P | Hybrid |', '|---|---:|---:|---:|']
        for r in cityres:
            for b,label in [('history_count','K=history count'),('5pct','K=5%'),('20pct','K=20%')]:lines.append(f"| {r['scope']} / {label} | {r[b+'_history']} | {r[b+'_model']} | {r[b+'_hybrid']} |")
        lines += ['', 'Same equal-budget hits restricted to DEV-positive routes with no FIT route history (history-only is zero by definition):', '', '| Scope / budget | History | Model P | Hybrid |', '|---|---:|---:|---:|']
        for r in cityres:
            for b,label in [('new_history_count','K=history count'),('new_5pct','K=5%'),('new_20pct','K=20%')]:lines.append(f"| {r['scope']} / {label} | {r[b+'_history']} | {r[b+'_model']} | {r[b+'_hybrid']} |")
        lines += ['', 'Alert burden, share of routes at medium/high (mean [95% day bootstrap CI]):', '', '| Scope / day type | History | Model P | Hybrid |', '|---|---:|---:|---:|']
        for r in cityres:
            for typ,label in [('flood','DEV record days'),('rain_no_record','rainy-season no-record days'),('dry_no_record','dry-season days')]:lines.append(f"| {r['scope']} / {label} | {r[typ+'_history']} | {r[typ+'_model']} | {r[typ+'_hybrid']} |")
        lines.append('')
    Path('reports/dev_eval.md').write_text('\n'.join(lines)+'\n')
    pd.DataFrame(outputs).to_csv('reports/dev_results.tsv',sep='\t',index=False)
    print(f"wrote reports/dev_eval.md and reports/dev_results.tsv; {len(outputs)} city/scope rows")

if __name__=='__main__':run()

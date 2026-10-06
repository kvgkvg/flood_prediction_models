#!/usr/bin/env python3
"""One-shot scoring of the explicitly unlocked 2025+ holdout."""
from __future__ import annotations
import argparse, datetime as dt, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from eval_dev import boot_mean, fmt, auc_ci, fmt_auc, _cause_level, _top
from floodrisk.combine import route_bands

FINAL=Path('models/final_2025-01-01'); MARK=FINAL/'LOCKED_TEST_USED'
CITY_NAMES=('ho_chi_minh','da_nang')

def git_hash():
    try:return subprocess.check_output(['git','rev-parse','--short','HEAD'],text=True).strip()
    except Exception:return 'unknown'
def _records():
    x=pd.read_parquet('data/processed/flood_records.parquet',columns=['record_id','city','date','cause','split','lat','lon','location_precision','road_name_text'],filters=[('split','==','test_locked')])
    x['date']=pd.to_datetime(x.date,errors='coerce').dt.normalize()
    return x[x.date>=pd.Timestamp('2025-01-01')].copy()
def _undated_records():
    # Only location, road text and id are used, and only by D6 pure route ranking.
    return pd.read_parquet('data/processed/flood_records.parquet',columns=['record_id','city','split','lat','lon','location_precision','road_name_text'],filters=[('split','==','test_locked_undated')])
def _matches(records):
    if records.empty:return pd.DataFrame(columns=list(records.columns)+['route_id'])
    ids=records.record_id.astype(str).unique().tolist();d=ds.dataset('data/processed/flood_record_matches.parquet',format='parquet')
    x=d.to_table(columns=['record_id','route_id'],filter=ds.field('record_id').isin(ids)).to_pandas().dropna(subset=['route_id'])
    x.record_id=x.record_id.astype(str);x.route_id=x.route_id.astype(str)
    missing=records.loc[~records.record_id.astype(str).isin(x.record_id)].copy()
    if len(missing):
        import geopandas as gpd
        from shapely.geometry import Point
        from pyproj import Transformer
        from floodrisk.records import normalize_name
        from floodrisk.matching import _parse_street,_similar
        from functools import lru_cache
        results=[]
        for city,g in missing.groupby('city',sort=True):
            routes=gpd.read_parquet(Path('data/processed')/city/'routes.parquet',columns=['route_id','name_norm','named','geometry'])
            metric=32648 if city=='ho_chi_minh' else 32649
            routes=routes.to_crs(metric);sidx=routes.sindex
            transformer=Transformer.from_crs(4326,metric,always_xy=True)
            for row in g.itertuples(index=False):
                if pd.isna(row.lat) or pd.isna(row.lon):
                    results.append({'record_id':str(row.record_id),'route_id':None});continue
                px,py=transformer.transform(float(row.lon),float(row.lat));point=Point(px,py)
                norm=normalize_name(_parse_street(row.road_name_text));radius=500 if row.location_precision in ('street','area') and norm else 150
                candidates=sidx.query(point.buffer(radius),predicate='intersects');near=[]
                for j in candidates:
                    geom=routes.geometry.iloc[int(j)];dist=point.distance(geom)
                    if dist<=radius:near.append((dist,int(j)))
                names=[(dist,j) for dist,j in near if bool(routes.iloc[j].named) and _similar(norm,routes.iloc[j].name_norm)>=.55]
                if names:dist,j=min(names,key=lambda z:(z[0],str(routes.iloc[z[1]].route_id)))
                else:
                    close=[(dist,j) for dist,j in near if dist<=40]
                    if close:dist,j=min(close,key=lambda z:(z[0],str(routes.iloc[z[1]].route_id)))
                    else:j=None
                results.append({'record_id':str(row.record_id),'route_id':str(routes.iloc[j].route_id) if j is not None else None})
        x=pd.concat([x,pd.DataFrame(results)],ignore_index=True)
    return records.merge(x,on='record_id',how='left')
def _bootstrap_auc(y,p,seed):
    return auc_ci(y,p,seed=seed,draws=2000)
def _metricrow(city,scope,metric,method,values,n_days,n_records,new=False):
    value=fmt(values)
    return {'city':city,'scope':scope,'metric':metric,'method':method,'population':'NEW' if new else 'overall','estimate_95ci':value,'n_flood_days':n_days,'n_records':n_records}
def _valid_levels(band,t,th):return _cause_level(band,t,th)

def pilot():
    # Input-only rehearsal: deliberately do not open flood_records or matches.
    for city in CITY_NAMES:
        p=FINAL/city/'route_susceptibility.parquet';r=pd.read_parquet(p,columns=['route_id','in_universe','S_hyb_rain'],engine='pyarrow').head(32)
        q=pd.read_parquet(Path('data/processed/rain_percentiles_locked')/f'{city}_ifs.parquet',columns=['date','T_rain'])
        assert q.date.max()>=pd.Timestamp('2025-01-01') and np.isfinite(q.loc[q.date>='2025-01-01','T_rain']).any()
        print(f'pilot {city}: sample routes={len(r)}, IFS dates={len(q)}; no holdout labels/attributes loaded')

def run(force=False,pilot_mode=False):
    if pilot_mode:return pilot()
    FINAL.mkdir(parents=True,exist_ok=True)
    if MARK.exists() and not force:raise RuntimeError(f'locked evaluation already marked at {MARK}; pass --force only for a documented bug-fix rerun')
    marker={'started_at':dt.datetime.now().astimezone().isoformat(),'git_hash':git_hash(),'config_sha256':subprocess.check_output(['sha256sum','models/final_config.json'],text=True).split()[0],'rain_source':'IFS percentile CDF frozen before 2025','locked_test_read':True}
    MARK.write_text(json.dumps(marker,indent=2)+'\n')
    # Marker is durable before the first locked record is opened.
    rec=_records();undated=_undated_records();matched=_matches(rec);undated_matched=_matches(undated)
    thresholds=json.loads(Path('models/combination_thresholds.json').read_text())['thresholds']
    config=json.loads(Path('models/final_config.json').read_text());thresholds={c:dict(v) for c,v in thresholds.items()}
    for c in thresholds:thresholds[c]['rain']={'t_lo':config['q_watch'],'t_hi':config['q_alert']}
    allrows=[];cityinfo={};report=['# Locked test evaluation (used once)','',f"Marker: `{MARK}`; started {marker['started_at']}; git {marker['git_hash']}. Model/config were frozen before evaluation. Rain: IFS CDF reference uses dates < 2025-01-01. Intervals bootstrap flood days (2,000 draws); D3 non-event intervals bootstrap calendar days and D4 bootstraps event/non-event days.",'','Unreported days are not verified dry. Levels follow the frozen two-factor rule; the trigger was day-fitted, so applying it to hourly windows in the runner remains an approximation.','']
    for city in CITY_NAMES:
        columns=['route_id','in_universe','S_rain','S_tide','S_hyb_rain','S_hyb_tide','H_rain','H_tide','H_any']
        s=pd.read_parquet(FINAL/city/'route_susceptibility.parquet',columns=columns);s.route_id=s.route_id.astype(str);ids=s.route_id.to_numpy();n=len(s);lookup={r:i for i,r in enumerate(ids)}
        uni=s.in_universe.to_numpy(bool);hist=s.H_any.to_numpy(bool);hr=s.H_rain.to_numpy(bool);ht=s.H_tide.to_numpy(bool)
        sr=s.S_rain.to_numpy(np.float32);st=s.S_tide.to_numpy(np.float32);shr=s.S_hyb_rain.to_numpy(np.float32);sht=s.S_hyb_tide.to_numpy(np.float32)
        model_score=np.maximum(sr,st);hybrid_score=np.maximum(shr,sht)
        scope_masks={'all':np.ones(n,bool),'in_universe':uni};bands={}
        for scope,mask in scope_masks.items():bands[scope]={'mr':route_bands(sr,sr,mask),'mt':route_bands(st,st,mask),'hr':route_bands(shr,sr,mask),'ht':route_bands(sht,st,mask)}
        d=rec[rec.city==city];m=matched[matched.city==city];um=undated_matched[undated_matched.city==city]
        rain_record_days=set(pd.to_datetime(d.loc[d.cause.isin(['rain','combined']),'date']).dt.normalize())
        tide_record_days=set(pd.to_datetime(d.loc[d.cause.isin(['tide','combined']),'date']).dt.normalize())
        day_routes={}
        for day,g in m.groupby('date'):
            routes={}
            for rid,cause in zip(g.route_id,g.get('cause',pd.Series(['rain']*len(g)))):routes.setdefault(str(rid),set()).add(str(cause))
            day_routes[pd.Timestamp(day)]=routes
        rain=pd.read_parquet(Path('data/processed/rain_percentiles_locked')/f'{city}_ifs.parquet',columns=['date','T_rain']);rain.date=pd.to_datetime(rain.date).dt.normalize()
        if city=='ho_chi_minh':
            tide=pd.read_parquet(Path('data/processed')/city/'trigger_daily.parquet',columns=['date','T_tide']);tide.date=pd.to_datetime(tide.date).dt.normalize();daily=tide.set_index('date').join(rain.set_index('date'),how='inner')
        else:
            daily=rain.set_index('date');daily['T_tide']=0.
        days=[x for x in pd.date_range('2025-01-01',daily.index.max(),freq='D') if x in daily.index]
        eventdays=set(d.date.dropna().unique());season=lambda x:(5<=x.month<=11) if city=='ho_chi_minh' else (9<=x.month<=12)
        samples={'event':len(eventdays),'records':len(d),'matched_records':int(m.route_id.notna().sum()),'records_unmatched':int(m.route_id.isna().sum()),'undated_records':len(undated[undated.city==city]),'undated_matched':int(um.route_id.notna().sum()),'undated_unmatched':int(um.route_id.isna().sum())}
        results=[];hit={sc:{x:[] for x in ['model','history','hybrid','new_model','new_history','new_hybrid']} for sc in scope_masks}
        budgets={sc:{k:{x:[] for x in ['model','history','hybrid']} for k in ['history_count','5pct','20pct']} for sc in scope_masks};budgets_new={sc:{k:{x:[] for x in ['model','history','hybrid']} for k in ['history_count','5pct','20pct']} for sc in scope_masks}
        d6={sc:{k:[] for k in ['5_all','20_all','5_new','20_new']} for sc in scope_masks}
        burden={sc:{typ:{x:[] for x in ['model','history','hybrid','new_model','new_history','new_hybrid']} for typ in ['flood','rain_no_report','dry']} for sc in scope_masks}
        alerts={sc:{meth:[] for meth in ['model','history','hybrid']} for sc in scope_masks};alerts_new={sc:{meth:[] for meth in ['model','history','hybrid']} for sc in scope_masks}
        rain_states=[];tide_states=[];rain_t=[];tide_t=[];rain_y=[];tide_y=[];any_y=[]
        bydate={x:day_routes.get(x,{}) for x in days}
        for day in days:
            q=daily.loc[day];tr=float(q.T_rain);tt=float(q.T_tide);event=day in eventdays;mp=bydate[day]
            rain_states.append(0 if tr<thresholds[city]['rain']['t_lo'] else 1 if tr<thresholds[city]['rain']['t_hi'] else 2);rain_t.append(tr);rain_y.append(day in rain_record_days);any_y.append(event)
            if city=='ho_chi_minh':tide_states.append(0 if tt<thresholds[city]['tide']['t_lo'] else 1 if tt<thresholds[city]['tide']['t_hi'] else 2);tide_t.append(tt);tide_y.append(day in tide_record_days)
            for scope,mask in scope_masks.items():
                ix=np.flatnonzero(mask);b=bands[scope];fresh=mask&~hist
                cause_lev={
                  'model':(_valid_levels(b['mr'],tr,thresholds[city]['rain']),_valid_levels(b['mt'],tt,thresholds[city]['tide'])),
                  'hybrid':(_valid_levels(b['hr'],tr,thresholds[city]['rain']),_valid_levels(b['ht'],tt,thresholds[city]['tide']))}
                lev={
                  'model':np.maximum(*cause_lev['model']),
                  'hybrid':np.maximum(*cause_lev['hybrid']),
                  'history':hist.astype(np.uint8)}
                for method,l in lev.items():
                    alerts[scope][method].append(float(np.mean(l[mask]>=1)));alerts_new[scope][method].append(float(np.mean(l[fresh]>=1)) if fresh.any() else np.nan)
                positives=[]
                for rid,causes in mp.items():
                    if rid not in lookup or not mask[lookup[rid]]:continue
                    cs=[c for c in ('rain','tide') if c in causes or 'combined' in causes]
                    if not cs:cs=['rain','tide']
                    positives.append((lookup[rid],cs))
                if event and positives:
                    freshflags=np.asarray([not hist[j] for j,cs in positives],bool)
                    for method in ('model','history','hybrid'):
                        levday=lev[method];vals=[]
                        for j,cs in positives:
                            if method=='history':vals.append(bool(any(hr[j] if c=='rain' else ht[j] for c in cs)))
                            else:vals.append(bool(any(cause_lev[method][0 if c=='rain' else 1][j]>=1 for c in cs)))
                        vals=np.asarray(vals,bool);hit[scope][method].append(float(vals.mean()));hit[scope]['new_'+method].append(float(vals[freshflags].mean()) if freshflags.any() else np.nan)
                    kh=int(hist[ix].sum());size=len(ix);routeids=[ids[j] for j,_ in positives];newids=[r for r,z in zip(routeids,freshflags) if z]
                    for key,k in [('history_count',kh),('5pct',max(1,int(np.ceil(.05*size)))),('20pct',max(1,int(np.ceil(.20*size))))]:
                        selections={'history':set(ids[ix[hist[ix]]]),'model':set(ids[_top(model_score,ix,k,model_score)]),'hybrid':set(ids[_top(hybrid_score,ix,k,model_score)])}
                        if key=='history_count' and kh:assert selections['hybrid']==selections['history'],f'{city}/{scope}: hybrid must rank history first at K=history size'
                        for method,chosen in selections.items():
                            budgets[scope][key][method].append(float(np.mean([r in chosen for r in routeids])))
                            budgets_new[scope][key][method].append(float(np.mean([r in chosen for r in newids])) if newids else np.nan)
                    # D6 is record-weighted; add locked-undated route records only here.
                    dated_routes=[str(x) for x in m.loc[m.date==day,'route_id'] if str(x) in lookup and mask[lookup[str(x)]]]
                    combined=dated_routes;newcombined=[r for r in combined if not hist[lookup[r]]]
                    for pct,k in [('5',max(1,int(np.ceil(.05*size)))),('20',max(1,int(np.ceil(.20*size))))]:
                        for key,route_set in [('all',combined),('new',newcombined)]:
                            chosen=set(ids[_top(hybrid_score,ix,k,model_score)]);d6[scope][f'{pct}_{key}'].append(float(np.mean([r in chosen for r in route_set])) if route_set else np.nan)
                typ='flood' if event else 'rain_no_report' if season(day) else 'dry'
                for method,l in lev.items():
                    burden[scope][typ][method].append(float(np.mean(l[mask]>=1)));burden[scope][typ]['new_'+method].append(float(np.mean(l[fresh]>=1)) if fresh.any() else np.nan)
        nf=len(eventdays);nr=samples['matched_records'];seed=4100+(0 if city=='ho_chi_minh' else 50)
        for scope in scope_masks:
            for method in ('model','history','hybrid'):
                results.append(_metricrow(city,scope,'D1',method,hit[scope][method],nf,nr))
                results.append(_metricrow(city,scope,'D1',method,hit[scope]['new_'+method],nf,nr,True))
                for typ in ('flood','rain_no_report','dry'):
                    results.append(_metricrow(city,scope,'D3_'+typ,method,burden[scope][typ][method],nf,nr))
                    results.append(_metricrow(city,scope,'D3_'+typ,method,burden[scope][typ]['new_'+method],nf,nr,True))
            for key in ('history_count','5pct','20pct'):
                for method in ('model','history','hybrid'):
                    results.append(_metricrow(city,scope,'D2_'+key,method,budgets[scope][key][method],nf,nr))
                    results.append(_metricrow(city,scope,'D2_'+key,method,budgets_new[scope][key][method],nf,nr,True))
            for pct in ('5','20'):
                for pop in ('all','new'):results.append(_metricrow(city,scope,'D6_top'+pct,'hybrid',d6[scope][pct+'_'+pop],nf,nr,pop=='new'))
        rain_auc=_bootstrap_auc(rain_y,rain_t,seed);rain_cov={k:float(np.mean(np.asarray(rain_states)==k)) for k in (0,1,2)}
        for method,val in [('trigger_rain_auc',rain_auc)]:results.append({'city':city,'scope':'day','metric':method,'method':'IFS_trigger','population':'all_days','estimate_95ci':fmt_auc(val),'n_flood_days':nf,'n_records':nr})
        if city=='ho_chi_minh':
            auc_tide=_bootstrap_auc(tide_y,tide_t,seed+1);results.append({'city':city,'scope':'day','metric':'trigger_tide_auc','method':'astronomical_tide','population':'tide_days','estimate_95ci':fmt_auc(auc_tide),'n_flood_days':int(sum(tide_y)),'n_records':int(m.cause.isin(['tide','combined']).sum())})
        event_mask=np.asarray([x in eventdays for x in days],bool);rain_mask=np.asarray(rain_y,bool);tide_mask=np.asarray(tide_y,bool) if city=='ho_chi_minh' else np.zeros(len(days),bool)
        for prefix,states,mask in [('rain',np.asarray(rain_states),event_mask),('rain_on_rain_days',np.asarray(rain_states),rain_mask)]:
            for code,state in enumerate(('quiet','watch','alert')):
                value=float(np.mean(states[mask]==code)) if mask.any() else np.nan
                results.append({'city':city,'scope':'day','metric':prefix+'_state_'+state,'method':'IFS_trigger','population':'locked_flood_days','estimate_95ci':f'{value:.3f}' if np.isfinite(value) else 'NA','n_flood_days':int(mask.sum()),'n_records':nr})
        if city=='ho_chi_minh':
            for code,state in enumerate(('quiet','watch','alert')):
                value=float(np.mean(np.asarray(tide_states)[tide_mask]==code)) if tide_mask.any() else np.nan
                results.append({'city':city,'scope':'day','metric':'tide_state_'+state,'method':'tide_trigger','population':'locked_tide_days','estimate_95ci':f'{value:.3f}' if np.isfinite(value) else 'NA','n_flood_days':int(tide_mask.sum()),'n_records':int(m.cause.isin(['tide','combined']).sum())})
        for scope,mask in scope_masks.items():
            ix=np.flatnonzero(mask);chosen5=set(ids[_top(hybrid_score,ix,max(1,int(np.ceil(.05*len(ix)))),model_score)]);chosen20=set(ids[_top(hybrid_score,ix,max(1,int(np.ceil(.20*len(ix)))),model_score)])
            urs=[str(x) for x in um.loc[um.route_id.notna(),'route_id'] if str(x) in lookup and mask[lookup[str(x)]]]
            if urs:
                for pct,chosen in [('5',chosen5),('20',chosen20)]:
                    hitrate=float(np.mean([r in chosen for r in urs]));results.append({'city':city,'scope':scope,'metric':'D6_undated_top'+pct,'method':'hybrid','population':'test_locked_undated','estimate_95ci':f'{hitrate:.3f} (no interval; undated)','n_flood_days':0,'n_records':len(urs)})
        # D4 city alert-index AUC, with bootstrap over flood/non-flood calendar days.
        y=np.asarray([x in eventdays for x in days],bool)
        for scope in scope_masks:
            for method in ('model','history','hybrid'):
                auc=_bootstrap_auc(y,alerts[scope][method],seed+2);results.append({'city':city,'scope':scope,'metric':'D4_alert_index_auc','method':method,'population':'all_days','estimate_95ci':fmt_auc(auc),'n_flood_days':nf,'n_records':nr})
        # Cause-stratified HCMC D7 values, day-weighted over days containing that cause.
        d7={}
        if city=='ho_chi_minh':
            for cause in ('rain','tide'):
                cs_days=set(pd.to_datetime(d.loc[d.cause.isin([cause,'combined']),'date']).dt.normalize());cause_records=m[m.cause.isin([cause,'combined'])]
                for scope,mask in scope_masks.items():
                    for method in ('model','history','hybrid'):
                        vals=[];newvals=[]
                        for day in sorted(cs_days):
                            mp=day_routes.get(day,{})
                            positives=[(lookup[r],causes) for r,causes in mp.items() if r in lookup and mask[lookup[r]] and (cause in causes or 'combined' in causes)]
                            if not positives:continue
                            tr=float(daily.loc[day].T_rain);tt=float(daily.loc[day].T_tide);b=bands[scope]
                            lv=_valid_levels(b['mr' if method=='model' else 'hr'],tr,thresholds[city]['rain']) if cause=='rain' else _valid_levels(b['mt' if method=='model' else 'ht'],tt,thresholds[city]['tide'])
                            flags=hr if cause=='rain' else ht
                            v=np.asarray([bool(flags[j]) if method=='history' else bool(lv[j]>=1) for j,ca in positives]);fresh=np.asarray([not hist[j] for j,ca in positives]);vals.append(v.mean());newvals.append(v[fresh].mean() if fresh.any() else np.nan)
                        d7[(cause,scope,method)]=(fmt(vals),fmt(newvals),len(cs_days),len(cause_records))
        cityinfo[city]={'samples':samples,'flood_days':nf,'records':nr,'rain_auc':rain_auc,'rain_coverage':rain_cov,'d7':d7,'results':results}
        allrows.extend(results)
        report += [f'## {city}', '',f"Dated locked records: {samples['records']} ({samples['matched_records']} matched, {samples['records_unmatched']} unmatched); distinct flood days: {nf}. Test-locked undated records: {samples['undated_records']} ({samples['undated_matched']} matched, {samples['undated_unmatched']} unmatched; ranking D6 only).",'', '| Scope | Method | D1 overall | D1 NEW | D2 at K=history / 5% / 20% overall | D2 NEW | D6 top 5% / 20% overall | D6 NEW |','|---|---|---:|---:|---:|---:|---:|---:|']
        for scope in ('all','in_universe'):
            for method in ('hybrid','model','history'):
                rr=[x for x in results if x['scope']==scope and x['metric']=='D1' and x['method']==method]
                get=lambda metric,pop='overall':next(x['estimate_95ci'] for x in results if x['scope']==scope and x['metric']==metric and x['method']==method and x['population']==pop)
                d6all=' / '.join(get('D6_top'+p) for p in ('5','20')) if method=='hybrid' else '—'
                d6new=' / '.join(get('D6_top'+p,'NEW') for p in ('5','20')) if method=='hybrid' else '—'
                vals=[' / '.join(get('D2_'+k) for k in ('history_count','5pct','20pct')),' / '.join(get('D2_'+k,'NEW') for k in ('history_count','5pct','20pct')),d6all,d6new]
                report.append(f"| {scope} | {method} | {rr[0]['estimate_95ci']} | {next(x['estimate_95ci'] for x in results if x['scope']==scope and x['metric']=='D1' and x['method']==method and x['population']=='NEW')} | "+' | '.join(vals)+' |')
        report += ['', '| Scope | Method | D3 flood-day burden | D3 rainy no-report burden | D3 dry-season burden |','|---|---|---:|---:|---:|']
        for scope in ('all','in_universe'):
            for method in ('hybrid','model','history'):
                vals=[next(x['estimate_95ci'] for x in results if x['scope']==scope and x['metric']=='D3_'+typ and x['method']==method and x['population']=='overall') for typ in ('flood','rain_no_report','dry')];report.append(f'| {scope} | {method} | '+' | '.join(vals)+' |')
        evmask=np.asarray([x in eventdays for x in days],bool);rainonly=np.asarray(rain_y,bool)
        event_cov={k:float(np.mean(np.asarray(rain_states)[evmask]==k)) for k in (0,1,2)} if evmask.any() else {0:np.nan,1:np.nan,2:np.nan}
        rain_cov_pos={k:float(np.mean(np.asarray(rain_states)[rainonly]==k)) for k in (0,1,2)} if rainonly.any() else {0:np.nan,1:np.nan,2:np.nan}
        report += ['',f"IFS rain-trigger AUC on rain-record days: {fmt_auc(rain_auc)} (rain days {int(rainonly.sum())}, dated records {nr}). Among all locked flood days, rain states are quiet/watch/alert {event_cov[0]:.1%}/{event_cov[1]:.1%}/{event_cov[2]:.1%}; among rain-record days {rain_cov_pos[0]:.1%}/{rain_cov_pos[1]:.1%}/{rain_cov_pos[2]:.1%}."]
        if city=='ho_chi_minh' and tide_y:
            tc={k:float(np.mean(np.asarray(tide_states)[np.asarray(tide_y,bool)]==k)) for k in (0,1,2)}
            report.append(f"HCMC tide-trigger AUC on tide-record days: {fmt_auc(_bootstrap_auc(tide_y,tide_t,seed+1))} (tide days {int(sum(tide_y))}); tide states quiet/watch/alert {tc[0]:.1%}/{tc[1]:.1%}/{tc[2]:.1%}.")
        if city=='ho_chi_minh':
            report += ['', '| Cause | Method | HCMC D7 overall | HCMC D7 NEW | flood days / records |','|---|---|---:|---:|---:|']
            for cause in ('rain','tide'):
                for method in ('hybrid','model','history'):
                    a,b,nd,nr0=d7[(cause,'in_universe',method)];report.append(f'| {cause} | {method} | {a} | {b} | {nd} / {nr0} |')
        report += ['']
        undated_rows=[x for x in results if x['scope']=='all' and x['metric'].startswith('D6_undated')]
        if undated_rows:
            report += ['Undated locked rows: D6 pure ranking only (no day interval): '+ '; '.join(f"{x['metric'].replace('D6_undated_','')}={x['estimate_95ci']} (n={x['n_records']})" for x in undated_rows)+'.','']
    report += ['## DEV comparison and interpretation','','The side-by-side point estimates and intervals are in the compact DEV comparison table below; the full DEV reports remain linked for their route/day denominators. Model and trigger variants were frozen before this single evaluation.','', '| City | Population | DEV IFS D1 hybrid | Locked D1 hybrid | DEV top-5 hybrid / locked top-5 | DEV dry burden / locked dry burden |','|---|---|---:|---:|---:|---:|']
    dev=pd.read_csv('reports/dev_results_ifs.tsv',sep='\t')
    def dev_value(city,scope,metric,pop='overall'):
        row=dev[(dev.city==city)&(dev.scope==scope)&(dev.metric==metric)&(dev.method=='hybrid')]
        return str(row.iloc[0]['overall' if pop=='overall' else 'new']) if len(row) else 'NA'
    for city in CITY_NAMES:
        for scope in ('all','in_universe'):
            d1=next(x['estimate_95ci'] for x in cityinfo[city]['results'] if x['scope']==scope and x['metric']=='D1' and x['method']=='hybrid' and x['population']=='overall')
            d6=next(x['estimate_95ci'] for x in cityinfo[city]['results'] if x['scope']==scope and x['metric']=='D6_top5' and x['population']=='overall')
            dry=next(x['estimate_95ci'] for x in cityinfo[city]['results'] if x['scope']==scope and x['metric']=='D3_dry' and x['method']=='hybrid' and x['population']=='overall')
            report.append(f'| {city} | {scope} | {dev_value(city,scope,"D1")} | {d1} | {dev_value(city,scope,"D6_top5")} / {d6} | {dev_value(city,scope,"D3_dry")} / {dry} |')
    report += ['', '## Undated locked records: ranking only','', 'The 2025+ undated rows are excluded from all day, trigger, level, history update, and D1/D2/D3/D4 calculations. They are included only in the record-weighted D6 ranking capture above; they have no flood-day bootstrap interval because they have no dates.','', '## What held up / what did not','', 'See results above. These are route captures under the recorded observation process, not verified flood probability or calibration. Unreported routes/days are not confirmed dry; sparse days yield wide bootstrap intervals. D6 reflects only matched report routes and ranking, not warning lead time.']
    Path('reports/locked_eval.md').write_text('\n'.join(report)+'\n');pd.DataFrame(allrows).to_csv('reports/locked_results.tsv',sep='\t',index=False)
    from refresh_locked_report import main as refresh_report
    refresh_report()
    print(f'wrote locked evaluation: {len(allrows)} metrics, cities={[ (c,cityinfo[c]["flood_days"],cityinfo[c]["records"]) for c in CITY_NAMES ]}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--force',action='store_true');a=p.parse_args();run(a.force,a.pilot)

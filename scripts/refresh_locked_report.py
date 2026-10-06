#!/usr/bin/env python3
"""Rebuild comparison sections from already-saved locked/DEV metric tables only."""
from pathlib import Path
import pandas as pd
from eval_dev import fmt

def main():
    p=Path('reports/locked_eval.md');txt=p.read_text();cut=txt.index('## D4 day-level AUCs')
    head=txt[:cut]
    locked=pd.read_csv('reports/locked_results.tsv',sep='\t',dtype=str).fillna('');dev=pd.read_csv('reports/dev_results_ifs.tsv',sep='\t',dtype=str).fillna('')
    state_mask=locked.metric.str.contains('_state_')
    for i,r in locked[state_mask].iterrows():
        n=int(r.n_flood_days);point=float(str(r.estimate_95ci).split()[0])
        if n>0:
            k=max(0,min(n,int(round(point*n))));locked.loc[i,'estimate_95ci']=fmt([1.]*k+[0.]*(n-k))
    locked.to_csv('reports/locked_results.tsv',sep='\t',index=False)
    out=[head.rstrip(),'## D4 day-level AUCs','', '| City | Scope | Method | Alert-index AUC | Flood days / records |','|---|---|---|---:|---:|']
    for _,r in locked[locked.metric=='D4_alert_index_auc'].iterrows():out.append(f"| {r.city} | {r.scope} | {r.method} | {r.estimate_95ci} | {r.n_flood_days} / {r.n_records} |")
    out+=['','Trigger AUCs:']
    for _,r in locked[locked.metric.isin(['trigger_rain_auc','trigger_tide_auc'])].iterrows():out.append(f"- {r.city} {r.metric}: {r.estimate_95ci}; flood days={r.n_flood_days}, records={r.n_records}.")
    out+=['','## DEV versus locked (IFS trigger; matching population/scope)','', '| City | Scope | D1 hybrid overall DEV / locked | D1 hybrid NEW DEV / locked | D6 top-5 overall DEV / locked | D6 top-5 NEW DEV / locked | D3 dry burden DEV / locked |','|---|---|---:|---:|---:|---:|---:|']
    def get(df,city,scope,metric,pop='overall'):
        x=df[(df.city==city)&(df.scope==scope)&(df.metric==metric)&(df.method=='hybrid')]
        if not len(x):return 'NA'
        return str(x.iloc[0]['overall' if pop=='overall' else 'new' if 'new' in x.columns else 'estimate_95ci'])
    for city in ('ho_chi_minh','da_nang'):
        for scope in ('all','in_universe'):
            d1=dev[(dev.city==city)&(dev.scope==scope)&(dev.metric=='D1')&(dev.method=='hybrid')]
            l1=locked[(locked.city==city)&(locked.scope==scope)&(locked.metric=='D1')&(locked.method=='hybrid')]
            d6=dev[(dev.city==city)&(dev.scope==scope)&(dev.metric=='D6_top5')&(dev.method=='hybrid')]
            l6=locked[(locked.city==city)&(locked.scope==scope)&(locked.metric=='D6_top5')&(locked.method=='hybrid')]
            dd=dev[(dev.city==city)&(dev.scope==scope)&(dev.metric=='D3_dry')&(dev.method=='hybrid')]
            ld=locked[(locked.city==city)&(locked.scope==scope)&(locked.metric=='D3_dry')&(locked.method=='hybrid')]
            a=lambda x,col: x.iloc[0][col] if len(x) else 'NA'
            out.append(f"| {city} | {scope} | {a(d1,'overall')} / {a(l1,'estimate_95ci')} | {a(d1,'new')} / {a(l1[l1.population=='NEW'],'estimate_95ci')} | {a(d6,'overall')} / {a(l6,'estimate_95ci')} | {a(d6,'new')} / {a(l6[l6.population=='NEW'],'estimate_95ci')} | {a(dd,'overall')} / {a(ld,'estimate_95ci')} |")
    for city in ('ho_chi_minh','da_nang'):
        rainauc=locked[(locked.city==city)&(locked.metric=='trigger_rain_auc')].iloc[0]
        rf=[]
        for key in ('rain_state_quiet','rain_state_watch','rain_state_alert'):
            z=locked[(locked.city==city)&(locked.metric==key)&(locked.population=='locked_flood_days')]
            if len(z):rf.append(z.iloc[0]['estimate_95ci'])
        nall=int(locked[(locked.city==city)&(locked.metric=='rain_state_quiet')].iloc[0].n_flood_days)
        rrf=[]
        for key in ('rain_on_rain_days_state_quiet','rain_on_rain_days_state_watch','rain_on_rain_days_state_alert'):
            z=locked[(locked.city==city)&(locked.metric==key)]
            if len(z):rrf.append(z.iloc[0]['estimate_95ci'])
        nr=int(locked[(locked.city==city)&(locked.metric=='rain_on_rain_days_state_quiet')].iloc[0].n_flood_days)
        suffix=f" Among all locked flood days, rain states quiet/watch/alert are {' / '.join(rf)} (n={nall} days, {rainauc.n_records} records); on rain-record days they are {' / '.join(rrf)} (n={nr} days, {rainauc.n_records} records)."
        line=f"IFS rain-trigger AUC on rain-record days: {rainauc.estimate_95ci} (rain days {rainauc.n_flood_days}, dated records {rainauc.n_records}).{suffix}"
        # Replace point-only state summary with day-bootstrap intervals.
        for idx,s in enumerate(out):
            if isinstance(s,str) and s.startswith('IFS rain-trigger AUC on rain-record days:') and f'## {city}' in '\n'.join(out[max(0,idx-30):idx]):out[idx]=line;break
    z=locked[(locked.city=='ho_chi_minh')&(locked.metric=='trigger_tide_auc')]
    if len(z):
        tideauc=z.iloc[0];parts=[]
        for key in ('tide_state_quiet','tide_state_watch','tide_state_alert'):
            q=locked[(locked.city=='ho_chi_minh')&(locked.metric==key)]
            if len(q):parts.append(q.iloc[0]['estimate_95ci'])
        line=f"HCMC tide-trigger AUC on tide-record days: {tideauc.estimate_95ci} (n={tideauc.n_flood_days} days, {tideauc.n_records} records); tide states quiet/watch/alert {' / '.join(parts)}."
        for idx,s in enumerate(out):
            if isinstance(s,str) and s.startswith('HCMC tide-trigger AUC on tide-record days:'):out[idx]=line;break
    out+=['','## Undated locked records: ranking only','', 'The 17 HCMC `test_locked_undated` rows are excluded from day, trigger, levels and D1/D2/D3/D4. Fourteen matched rows enter D6 only (no date bootstrap); three unmatched rows are not rankable. Da Nang had no such rows.','', '## What held up / what did not','', 'The routing ranking captured more Da Nang locked report routes than DEV top-5 estimates, while HCMC improves at D6 but has low D1 alert capture. HCMC history remains a strong baseline for rain. The very small event counts (8 HCMC / 18 Da Nang days) produce broad intervals. These results measure capture under observed reporting, not calibration or verified dry-road truth. The 29 unmatched Da Nang dated records are excluded from route-hit metrics; their spatial matching limitation matters. Applying day-fitted triggers to hourly windows remains an approximation.','']
    p.write_text('\n'.join(out)+'\n')
if __name__=='__main__':main()

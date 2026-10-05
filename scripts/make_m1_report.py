#!/usr/bin/env python3
"""Render frozen-baseline results and train-only transfer diagnostics."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from floodrisk.evalm1 import load_data,run_importance

TASKS=['T1','T2','T3','T4','T5'];METRICS=['strat_recall_at_10','recall_at_10','strat_auc','auc','average_precision','lift_at_10','strat2_recall_at_10']
def fmt(x):
    if not np.isfinite(x):return 'NA'
    return f'{x:.3f}'
def cell(task,key):
    p=task['point'].get(key,np.nan);ci=task['ci'].get(key,[np.nan,np.nan])
    return f'{fmt(p)} [{fmt(ci[0])}, {fmt(ci[1])}]'

def main():
    path=Path('reports/m1_details.json')
    if not path.exists():raise SystemExit('No scorer runs found; run scripts/eval_m1.py --scorer all first')
    details=json.loads(path.read_text());rows=sorted((dict(v,scorer=k) for k,v in details.items()),key=lambda x:x['HEADLINE'],reverse=True)
    out=['# Model 1 frozen baseline evaluation','','Reproduce scorer runs: `PYTHONPATH=src .venv/bin/python scripts/eval_m1.py --scorer all`; report: `PYTHONPATH=src .venv/bin/python scripts/make_m1_report.py`. Fixed seed 41073; each reported metric interval uses 1,000 label-stratified bootstrap draws. No locked records or labels were read.','', 'The headline is the mean of T1, T2 and T3 `strat_recall_at_10`; HEADLINE2 substitutes the built-up-tercile-controlled `strat2_recall_at_10`. All metrics are descriptive baseline comparisons on in-universe routes. HEADLINE interval brackets below are the means of the three task-specific bootstrap limits (a conservative task-interval envelope, not a joint bootstrap of the headline scalar).','', '## Headline ranking','','| Rank | Scorer | HEADLINE (task-CI envelope) | HEADLINE2 | Runtime (s) | Peak RSS (MB) | Features |','|---:|---|---:|---:|---:|---:|---:|']
    for i,r in enumerate(rows,1):
        lows=[];highs=[]
        for t in ('T1','T2','T3'):
            ci=r['tasks'][t]['ci']['strat_recall_at_10'];lows.append(ci[0]);highs.append(ci[1])
        out.append(f"| {i} | {r['scorer']} | {r['HEADLINE']:.3f} [{np.mean(lows):.3f}, {np.mean(highs):.3f}] | {r['HEADLINE2']:.3f} | {r['runtime_seconds']:.1f} | {r['peak_rss_mb']:.1f} | {r['n_features']} |")
    for task in TASKS:
        out+=['',f'## {task}: '+{'T1':'HCMC → Da Nang rain','T2':'Da Nang → HCMC rain','T3':'HCMC tide, spatial blocks','T4':'HCMC rain, spatial blocks','T5':'Da Nang rain, spatial blocks'}[task],'','| Scorer | strat recall@10 | raw recall@10 | strat AUC | AUC | AP | lift@10 | strat2 recall@10 |','|---|---:|---:|---:|---:|---:|---:|---:|']
        for r in sorted(rows,key=lambda x:x['HEADLINE'],reverse=True):
            t=r['tasks'][task];out.append('| '+r['scorer']+' | '+' | '.join(cell(t,m) for m in METRICS)+' |')
        out+=['','### Road-class group metrics','','| Scorer | Group | Recall@10 | AUC | AP | Lift@10 |','|---|---|---:|---:|---:|---:|']
        for r in sorted(rows,key=lambda x:x['HEADLINE'],reverse=True):
            t=r['tasks'][task]
            for group in ('major','mid','minor'):
                out.append(f"| {r['scorer']} | {group} | {cell(t,group+'_recall')} | {cell(t,group+'_auc')} | {cell(t,group+'_ap')} | {cell(t,group+'_lift')} |")
        if task=='T5':
            out+=['','Non-event-only positive-route stratified recall at 10%:']
            out += [f"- {r['scorer']}: {cell(r['tasks'][task],'non_event_strat_recall_at_10')}" for r in rows]
    out+=['','## LightGBM gain importances for the best three scorers','']
    for r in rows[:3]:
        name=r['scorer'];
        if name not in {'lgbm_design','lgbm_all','lgbm_all_cityrank','lgbm_phys_cityrank'}:
            out += [f'### {name}','', 'This winning scorer is not LightGBM; no LightGBM gain importance is attributed to its predictions.','']
            continue
        imp=run_importance(name,'ever_flood_rain','ho_chi_minh')
        out += [f'### {name}: HCMC rain training fit','', '| Rank | Feature | Gain |','|---:|---|---:|']
        out += [f'| {i} | {feat} | {gain:.3f} |' for i,(feat,gain) in enumerate(imp,1)]
    out+=['','## Cross-city feature-distribution shift (train-label fits only)','', 'For each transfer direction, features are ranked by LightGBM gain on the source city rain labels. KS compares the raw feature distributions and the matching cityrank distributions between cities; no target-city labels are used.']
    data={c:load_data(c) for c in ('ho_chi_minh','da_nang')}
    for tid,source in [('T1','ho_chi_minh'),('T2','da_nang')]:
        importance=run_importance('lgbm_all','ever_flood_rain',source);a=data['ho_chi_minh'];b=data['da_nang']
        out += ['',f'### {tid} source: {source}','', '| Source-ranked feature | Gain | Raw KS | Cityrank KS |','|---|---:|---:|---:|']
        n=0
        for feat,gain in importance:
            if feat not in a or feat not in b or not pd.api.types.is_numeric_dtype(a[feat]) or not pd.api.types.is_numeric_dtype(b[feat]):continue
            raw=ks_2samp(a[feat].dropna(),b[feat].dropna()).statistic
            rankcol=feat+'_cityrank'
            rank=ks_2samp(a[rankcol].dropna(),b[rankcol].dropna()).statistic if rankcol in a and rankcol in b else np.nan
            out.append(f'| {feat} | {gain:.3f} | {raw:.3f} | {fmt(rank)} |');n+=1
            if n>=15:break
    out += ['', '## Interpretation notes','', '- Road-class-only raw recall can be high when reporting concentrates on particular road classes. The headline stratifies within major/mid/minor groups; the three-class-only synthetic test returns about 10% stratified recall.','- Unknown routes are treated as negatives with sample weight 0.2, per design; routes with an eligible observation but no target-cause positive receive weight 1.0.','- T3–T5 use 2 km UTM blocks assigned to five folds by fixed seed; block identifiers and coordinates remain inside the harness.','- This report is baseline evidence only. It does not use 2025+ records and it does not train a production model.','']
    Path('reports/m1_baselines.md').write_text('\n'.join(out))
    print(f"wrote reports/m1_baselines.md; scorers={len(rows)}")
if __name__=='__main__':main()

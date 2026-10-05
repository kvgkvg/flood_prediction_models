#!/usr/bin/env python3
"""Generate the v2 descriptive baseline ranking from training-only run details."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

def fmt(v): return f'{v:.3f}' if np.isfinite(v) else 'NA'
def main():
    d=json.loads(Path('reports/m1_details.json').read_text());history=pd.read_csv('reports/m1_results.tsv',sep='\t').fillna('');latest=history.drop_duplicates('scorer',keep='last').set_index('scorer').to_dict('index')
    rows=[]
    for k,v in d.items():
        if not all(t in v['tasks'] for t in ('T1','T2','T3')):continue
        meta=latest.get(k,{})
        rows.append(dict(v,scorer=k,decision=meta.get('decision','baseline'),vs_best=meta.get('vs_best','')))
    rows.sort(key=lambda r:r['PRIMARY'],reverse=True)
    out=['# Model 1 v2 experiment leaderboard','','Reproduce baseline refresh: `PYTHONPATH=src .venv/bin/python scripts/eval_m1.py --scorer all --tasks T1,T2,T3 --n-boot 100`; reproduce this report with `PYTHONPATH=src .venv/bin/python scripts/make_m1_report.py`. A 100-draw refresh was used for all rows; paired candidate comparisons also used 100 draws. All labels are train/train_undated only. Locked records were not loaded.','', 'PRIMARY is the mean propensity-stratified recall@10 over T1–T3. HEADLINE is road-class-stratified recall@10 and HEADLINE2 further stratifies by built-up tercile. Each reported PRIMARY and HEADLINE interval is a joint route bootstrap over the three tasks. `vs_best` is paired PRIMARY delta and interval versus the current best at experiment time.','', '| Rank | Scorer | Decision | PRIMARY [95% CI] | HEADLINE [95% CI] | HEADLINE2 | vs_best PRIMARY delta [95% CI], P | Runtime s |','|---:|---|---|---:|---:|---:|---|---:|']
    for i,r in enumerate(rows,1):out.append(f"| {i} | {r['scorer']} | {r.get('decision','baseline')} | {r['PRIMARY']:.3f} [{fmt(r['PRIMARY_ci'][0])}, {fmt(r['PRIMARY_ci'][1])}] | {r['HEADLINE']:.3f} [{fmt(r['HEADLINE_ci'][0])}, {fmt(r['HEADLINE_ci'][1])}] | {r['HEADLINE2']:.3f} | {r.get('vs_best','')} | {r['runtime_seconds']:.1f} |")
    for t,title in [('T1','HCMC → Da Nang rain'),('T2','Da Nang → HCMC rain'),('T3','HCMC tide, spatial blocks')]:
        out+=['',f'## {t}: {title}','','| Scorer | Decision | Propensity recall@10 | Propensity AUC | Urban recall@10 | Road-class strat recall@10 | Raw recall@10 |','|---|---|---:|---:|---:|---:|---:|']
        for r in rows:
            x=r['tasks'][t];p=x['point'];c=x['ci'];out.append(f"| {r['scorer']} | {r.get('decision','baseline')} | {fmt(p['prop_recall_at_10'])} [{fmt(c['prop_recall_at_10'][0])}, {fmt(c['prop_recall_at_10'][1])}] | {fmt(p['prop_auc'])} [{fmt(c['prop_auc'][0])}, {fmt(c['prop_auc'][1])}] | {fmt(p['urban_recall_at_10'])} | {fmt(p['strat_recall_at_10'])} | {fmt(p['recall_at_10'])} |")
    out+=['','## What worked, what did not, and why','','- The prior best remained `lgbm_phys_cityrank` (PRIMARY 0.331), with terrain, water and non-built-up land cover ranked by city. None of the 12 candidates met both P(new > best) ≥ 0.90 and HEADLINE drop ≤ 0.01.','- PU bagging, exposure-matched negative sampling, exposure nuisance replacement, monotone constraints, compact features, physical logistic/spline models, rank averaging, shallow boosting, ExtraTrees, histogram boosting, and terrain/water-only all lost paired PRIMARY. Matching on exposure likely discarded useful physical contrasts as well as nuisance structure; compact/linear/tree alternatives did not recover a stable transfer gain at this label volume.','- The exposure-only baseline had PRIMARY 0.124, well below the physical best, but raw HEADLINE 0.219 shows appreciable reporting structure remains. Propensity control does not remove all exposure/label noise.','', '## Assumptions and skipped ideas','','- Exposure outcome is whether a route has an eligible training/undated report (`n_records` present); the 5-fold logistic propensity model is cross-fitted over the evaluated city universe using only exposure variables. Deciles define the strata.','- `exposure_only` predicts that exposure outcome from the same allowed exposure predictors.','- Cross-city stable feature filtering was skipped because it requires label-informed agreement in the target city, which would leak test labels. Date-count weighting was skipped because the frozen scorer interface does not expose `n_distinct_dates`. New feature engineering was skipped to preserve the fixed feature inputs.','- Per-task intervals use stratified route bootstrap. PRIMARY and HEADLINE intervals are joint across T1–T3. This is descriptive baseline evidence only; no locked data was evaluated.','']
    Path('reports/m1_leaderboard.md').write_text('\n'.join(out));print(f"wrote reports/m1_leaderboard.md; {len(rows)} scorers")
if __name__=='__main__':main()

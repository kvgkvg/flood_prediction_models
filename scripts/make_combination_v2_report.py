#!/usr/bin/env python3
"""Render FIT-only two-factor threshold settings and trade-off curves."""
import json
from pathlib import Path

x=json.loads(Path('models/combination_thresholds.json').read_text())
lines=['# Combination v2 FIT thresholds and trade-offs','','Route levels use A=top 5%, B=next 15%, C=rest. For each cause, FIT-only T thresholds define quiet (T<t_lo), watch (t_lo<=T<t_hi), alert (T>=t_hi). High=alert+A; medium=alert+B or watch+A. The requested FIT goals are alert coverage >=70% of positive days and quiet coverage >=80% of rainy-season no-report days. Threshold curves use FIT days only; DEV was not used for selection.','', 'This replaces quantiles of P over FIT flood-day route vectors. The old rule used different population cutoffs: HCMC all-route medium=0.0449 versus in-universe=0.4033; the 44 matched in-universe DEV routes had max P=0.0709 (zero above the universe cutoff), while 11 crossed the all-route cutoff. OOU routes did not have higher P (one matched OOU route, P=0; OOU route-day p95=0). HCMC DEV positive T maxima were 0.068 rain and 0.061 tide versus FIT positive maxima 0.153 and 0.911.','']
for city,causes in x['thresholds'].items():
    lines += [f'## {city}','','| Cause | t_lo | t_hi | FIT positives | FIT rainy-season no-report days | Alert sensitivity | Quiet specificity | Both goals met? |','|---|---:|---:|---:|---:|---:|---:|---|']
    for cause,p in causes.items():
        lines.append(f"| {cause} | {p['t_lo']:.6g} | {p['t_hi']:.6g} | {p['n_fit_positive_days']} | {p['n_fit_no_report_days']} | {p['selected_alert_sensitivity']:.1%} | {p['selected_quiet_specificity']:.1%} | {'yes' if p['targets_met'] else 'no'} |")
    for cause,p in causes.items():
        curve=p.get('tradeoff',[])
        lines += ['',f'### {cause}: threshold trade-off (sampled points; full empirical curve is in `models/combination_thresholds.json`)','','| t_hi | t_lo giving best quiet coverage with minimum gap | Positive days alerted | No-report days quiet |','|---:|---:|---:|---:|']
        if curve:
            take=sorted(set(round(i*(len(curve)-1)/10) for i in range(min(11,len(curve)))))
            for i in take:
                r=curve[i];lines.append(f"| {r['t_hi']:.6g} | {r['t_lo_for_best_quiet']:.6g} | {r['alert_sensitivity']:.1%} | {r['quiet_specificity']:.1%} |")
        else:lines.append('| no FIT positive days | — | — | — |')
    lines.append('')
lines += ['HCMC rain cannot meet both targets with the selected task-5 trigger and this rain source; its fitted compromise is shown above. Da Nang rain meets the arithmetic targets with only one FIT positive day, so the apparent 100% sensitivity is not a reliable estimate. Da Nang tide has no positives and is deliberately kept quiet.','', 'M1 refit used `lgbm_phys_cityrank`, in-universe routes, all positive/known-report routes, and a fixed-seed cap of 20,000 unlabeled routes per city. City-relative score for OOU routes is half their in-universe-reference percentile; a route with FIT history gets S_hist=0.80+0.20*min(1,n_distinct_dates/3), then S_hyb=max(S_model,S_hist).']
Path('reports/combination_v2.md').write_text('\n'.join(lines)+'\n')
print('wrote reports/combination_v2.md')

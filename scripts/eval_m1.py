#!/usr/bin/env python3
"""Run frozen Model 1 evaluation tasks and optional paired comparison."""
import argparse, json, resource, subprocess, sys
from pathlib import Path
import numpy as np
from floodrisk.evalm1 import evaluate_scorer,append_result,headline_bootstrap_difference

SCORERS=['random','elev_low','near_water','road_class','builtup','logreg_design','lgbm_design','lgbm_all','lgbm_all_cityrank','lgbm_phys_cityrank']

def rss_mb():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024

def main():
    p=argparse.ArgumentParser();p.add_argument('--scorer',required=True,choices=SCORERS+['all']);p.add_argument('--baseline');a=p.parse_args()
    if a.scorer=='all':
        if a.baseline:raise SystemExit('--baseline comparison requires one scorer per invocation')
        for name in SCORERS:
            cmd=[sys.executable,__file__,'--scorer',name]
            done=subprocess.run(cmd,check=False)
            if done.returncode:raise SystemExit(done.returncode)
        return
    run=evaluate_scorer(a.scorer);runs=[run]
    if a.baseline:
        if a.baseline not in SCORERS:raise SystemExit(f'unknown baseline {a.baseline}')
        base=evaluate_scorer(a.baseline);runs.append(base)
    git=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True,check=False).stdout.strip() or 'unknown'
    peak=rss_mb()
    for x in runs:append_result(x,git,peak)
    for x in runs:
        print(f"{x['scorer']}: HEADLINE={x['HEADLINE']:.4f} HEADLINE2={x['HEADLINE2']:.4f} runtime={x['runtime_seconds']:.1f}s features={x['n_features']}",flush=True)
    if a.baseline:
        mean,ci,pgt=headline_bootstrap_difference(run,runs[1])
        print(f"paired HEADLINE difference {a.scorer} - {a.baseline}: {mean:.4f} (95% CI {ci[0]:.4f}..{ci[1]:.4f}); P(A>B)={pgt:.3f}",flush=True)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Run frozen Model 1 evaluation tasks and optional paired comparison."""
import argparse, json, resource, subprocess, sys, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from floodrisk.evalm1 import evaluate_scorer,append_result

BASELINES=['random','elev_low','near_water','road_class','builtup','logreg_design','lgbm_design','lgbm_all','lgbm_all_cityrank','lgbm_phys_cityrank','exposure_only']
SCORERS=sorted(set(BASELINES+[p.stem for p in Path('experiments/m1').glob('*.py') if not p.stem.startswith('_')]))

def rss_mb():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024

def paired_primary(a,b,draws,seed=41073):
    rng=np.random.default_rng(seed);dif=[]
    for t in ('T1','T2','T3'):
        x=a['predictions'][t];z=b['predictions'][t].set_index('route_id').loc[x.route_id].reset_index()
        y=x.iloc[:,2].to_numpy(bool);e=x.propensity.to_numpy();groups=pd.qcut(pd.Series(e).rank(method='first'),q=10,labels=False,duplicates='drop').to_numpy()
        def score(s,w):
            hit=0.;npositive=float(np.sum(w*y))
            for g in np.unique(groups):
                ids=np.flatnonzero(groups==g);take=max(1,int(np.ceil(.1*len(ids))));top=ids[np.argsort(s[ids])[::-1][:take]];hit+=float(np.sum(w[top]*y[top]))
            return hit/max(1.,npositive)
        p=np.flatnonzero(y);n=np.flatnonzero(~y);sa=x.score.to_numpy();sb=z.score.to_numpy();reps=[]
        for _ in range(draws):
            ix=np.r_[rng.choice(p,len(p),True),rng.choice(n,len(n),True)];w=np.bincount(ix,minlength=len(y));reps.append(score(sa,w)-score(sb,w))
        dif.append(np.asarray(reps))
    d=np.mean(dif,axis=0)
    return float(np.mean(d)),np.quantile(d,[.025,.975]).tolist(),float(np.mean(d>0))

def cached_run(name,tasks,draws):
    module=Path('experiments/m1')/(name+'.py'); datafiles=[Path('data/processed')/c/f for c in ('ho_chi_minh','da_nang') for f in ('route_features.parquet','routes.parquet','route_labels.parquet')]
    signature='|'.join([hashlib.sha256(module.read_bytes()).hexdigest()]+[f'{p.stat().st_size}:{p.stat().st_mtime_ns}' for p in datafiles]+[','.join(tasks)])
    key=hashlib.sha256(signature.encode()).hexdigest()[:20];cache=Path('data/processed/m1_cache');cache.mkdir(parents=True,exist_ok=True);pp=cache/f'pred_{name}_{key}.pkl';details=json.loads(Path('reports/m1_details.json').read_text())
    if pp.exists() and name in details:
        item=details[name]
        return {'scorer':name,'description':item['description'],'PRIMARY':item['PRIMARY'],'PRIMARY_ci':item['PRIMARY_ci'],'HEADLINE':item['HEADLINE'],'HEADLINE_ci':item['HEADLINE_ci'],'HEADLINE2':item['HEADLINE2'],'runtime_seconds':0.,'predictions':pd.read_pickle(pp),'results':item['tasks'],'n_features':item['n_features']}
    run=evaluate_scorer(name,tasks,draws);pd.to_pickle(run['predictions'],pp);return run

def main():
    p=argparse.ArgumentParser();p.add_argument('--scorer',required=True,choices=SCORERS+['all']);p.add_argument('--baseline');p.add_argument('--tasks',default='T1,T2,T3,T4,T5');p.add_argument('--n-boot',type=int,default=1000);a=p.parse_args()
    if a.scorer=='all':
        if a.baseline:raise SystemExit('--baseline comparison requires one scorer per invocation')
        for name in SCORERS:
            cmd=[sys.executable,__file__,'--scorer',name,'--tasks',a.tasks,'--n-boot',str(a.n_boot)]
            done=subprocess.run(cmd,check=False)
            if done.returncode:raise SystemExit(done.returncode)
        return
    tasks=[x.strip() for x in a.tasks.split(',') if x.strip()];run=cached_run(a.scorer,tasks,a.n_boot);runs=[run]
    baseline_name=a.baseline
    is_candidate=a.scorer not in BASELINES
    if is_candidate and baseline_name is None:
        state=Path('models/m1_best.txt')
        if state.exists():baseline_name=state.read_text().strip()
        else:raise SystemExit('candidate run requires models/m1_best.txt or --baseline')
    if baseline_name:
        if baseline_name not in SCORERS:raise SystemExit(f'unknown baseline {baseline_name}')
        base=cached_run(baseline_name,tasks,a.n_boot);runs.append(base)
    git=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True,check=False).stdout.strip() or 'unknown'
    peak=rss_mb()
    decision='baseline';vs_best=''
    if is_candidate:
        delta,ci,pnew=paired_primary(run,runs[1],a.n_boot)
        head_delta=run['HEADLINE']-runs[1]['HEADLINE']
        decision='keep' if pnew>=.90 and head_delta>=-.01 else 'discard'
        vs_best=f'{delta:.5f} [{ci[0]:.5f},{ci[1]:.5f}],P={pnew:.3f}'
        if decision=='keep':
            Path('models').mkdir(exist_ok=True);Path('models/m1_best.txt').write_text(a.scorer+'\n')
        print(f"paired PRIMARY delta={vs_best}; HEADLINE delta={head_delta:.5f}; decision={decision}",flush=True)
    append_result(run,git,peak,decision=decision,vs_best=vs_best)
    for x in runs:
        print(f"{x['scorer']}: PRIMARY={x['PRIMARY']:.4f} HEADLINE={x['HEADLINE']:.4f} HEADLINE2={x['HEADLINE2']:.4f} runtime={x['runtime_seconds']:.1f}s features={x['n_features']}",flush=True)
if __name__=='__main__':main()

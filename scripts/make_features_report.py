#!/usr/bin/env python3
"""Descriptive single-feature ranking audit; no model is trained."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

SEED=264; BOOT=100

def score_feature(x,y,seed):
    ok=pd.notna(x);x=np.asarray(x[ok],dtype=float);y=np.asarray(y[ok],dtype=bool)
    if len(np.unique(y))<2 or len(x)<5:return None
    vals,inv=np.unique(x,return_inverse=True);kbin=len(vals)
    pos=np.bincount(inv[y],minlength=kbin).astype(float);neg=np.bincount(inv[~y],minlength=kbin).astype(float)
    pn=pos.sum();nn=neg.sum();per_bin=np.cumsum(neg)-neg+.5*neg
    auc=float(np.dot(pos,per_bin)/(pn*nn));direction='high' if auc>=.5 else 'low';strength=max(auc,1-auc)
    k=max(1,int(np.ceil(.1*len(x))));ix=np.argsort(x if auc>=.5 else -x)[-k:];rec=float(y[ix].sum()/max(1,y.sum()))
    rng=np.random.default_rng(seed);pp=pos/pn;np_=neg/nn;boots=[]
    for _ in range(BOOT):
        bp=rng.multinomial(int(pn),pp);bn=rng.multinomial(int(nn),np_)
        boots.append(float(np.dot(bp,np.cumsum(bn)-bn+.5*bn)/(pn*nn)))
    ci=np.quantile(boots,[.025,.975]) if boots else [np.nan,np.nan]
    if auc<.5:ci=sorted((1-ci[1],1-ci[0]))
    return strength,float(ci[0]),float(ci[1]),rec,direction

def main():
    root=Path('data/processed');sections=['# Route feature descriptive report','','Reproducible command: `PYTHONPATH=src .venv/bin/python scripts/make_features_report.py` (seed 264, 100 stratified bootstrap draws per feature). No model fitting. Label metrics use only train/train_undated route labels, and only in-universe routes. Locked records are excluded; the only permitted locked output is aggregate record/date counts in routes_and_labels.md.','', 'ROC AUC is oriented to the better single-feature direction (`high` or `low`); intervals are stratified route bootstrap intervals. `recall_at_10pct` is the share of positive routes ranked in the most risk-indicative 10% by that feature. Rankings are descriptive and unadjusted for multiple comparisons.','']
    for city in ('ho_chi_minh','da_nang'):
        f=pd.read_parquet(root/city/'route_features.parquet');routes=pd.read_parquet(root/city/'routes.parquet');labels=pd.read_parquet(root/city/'route_labels.parquet')
        f=f.merge(routes[['route_id','in_universe']],on='route_id',how='left',suffixes=('','_r'))
        f['in_universe']=f.in_universe.fillna(f.in_universe_r).fillna(False).astype(bool);f=f.drop(columns=['in_universe_r'],errors='ignore')
        numeric=[c for c in f.select_dtypes(include='number').columns if c!='route_id' and not c.endswith('_cityrank') or c.endswith('_cityrank')]
        numeric=[c for c in numeric if c not in ('in_universe',)]
        sections += [f'## {city}','',f"- Routes with features: {len(f)}; in modelling universe: {int(f.in_universe.sum())}; feature columns excluding key and flag: {len([c for c in f.columns if c not in ('route_id','in_universe')])}."]
        feature_cols=[c for c in f.columns if c not in ('route_id','in_universe')]
        nulls=f[feature_cols].isna().mean().sort_values(ascending=False)
        sections.append('- Highest feature null rates: '+', '.join(f'{k} {v:.1%}' for k,v in nulls.head(10).items())+'.')
        sections += ['', '### Null rate by continuous feature', '', '| Feature | Null rate |', '|---|---:|']
        sections += [f'| {k} | {v:.1%} |' for k,v in nulls.items()]
        interpretable=[c for c in ['fab_elev_min','cop_elevation_min','fab_rel_elev_1000m_min','fab_fill_depth_max','fab_flow_accumulation_log_max','fab_twi_max','fab_dist_any_water_min','fab_hand_any_m_min','lc_builtup_200m_frac','lc_water_500m_frac','road_length_density_500m','road_intersections_300m'] if c in f]
        sections.append('### Interpretable feature summaries')
        sections.append('| Feature | Non-null | Mean | Median | P10–P90 |');sections.append('|---|---:|---:|---:|---:|')
        for c in interpretable:
            x=pd.to_numeric(f[c],errors='coerce').dropna();sections.append(f'| {c} | {len(x)} | {x.mean():.3f} | {x.median():.3f} | {x.quantile(.1):.3f}–{x.quantile(.9):.3f} |')
        for cause,flag in [('rain','ever_flood_rain'),('tide','ever_flood_tide')]:
            if city=='da_nang' and cause=='tide':continue
            ymap=labels.set_index('route_id')[flag].astype(bool);subset=f.loc[f.in_universe].copy();y=subset.route_id.map(ymap).fillna(False).to_numpy(bool)
            feats=[c for c in numeric if c in subset and subset[c].notna().sum()>10]
            scored=[]
            for j,c in enumerate(feats):
                out=score_feature(pd.to_numeric(subset[c],errors='coerce').to_numpy(),y,SEED+j)
                if out:scored.append((c,*out))
            scored.sort(key=lambda z:z[1],reverse=True)
            sections += [f'### {cause} univariate ranking (positive routes: {int(y.sum())})','', '| Rank | Feature | Better direction | ROC AUC (95% CI) | Recall at 10% |','|---:|---|---|---:|---:|']
            for rank,z in enumerate(scored[:15],1):sections.append(f'| {rank} | {z[0]} | {z[5]} | {z[1]:.3f} ({z[2]:.3f}–{z[3]:.3f}) | {z[4]:.1%} |')
            sections.append('')
            sections.append('Bottom five by oriented AUC: '+('; '.join(f'{z[0]} {z[1]:.3f} [{z[2]:.3f}, {z[3]:.3f}]' for z in sorted(scored,key=lambda z:z[1])[:5]) or 'not estimable')+'.')
            by={z[0]:z for z in scored}
            sections.append('Design baselines: '+ '; '.join(f"{name}: AUC {by[col][1]:.3f} [{by[col][2]:.3f}, {by[col][3]:.3f}], recall_at_10pct {by[col][4]:.1%}, direction {by[col][5]}" if col in by else f'{name}: unavailable' for name,col in [('lowest FABDEM elevation','fab_elev_min'),('proximity to any water','fab_dist_any_water_min')])+'.')
            sections.append('')
    Path('reports/features.md').write_text('\n'.join(sections)+'\n')
    print(f"wrote reports/features.md; bootstrap={BOOT}")
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Cutoff-controlled final artifact builder; never reads test_locked rows."""
from __future__ import annotations
import argparse,gc,json,os,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd

from floodrisk.combine import (fit_route_models,read_fit_records,join_matched_records,
    history_scores,percentile_score)
from fit_percentile_trigger import (CITIES,FIELDS,labels as rain_labels,fit_candidates,
    choose_states)

def write_config():
    old=Path('models/final_config.json')
    if old.exists():return json.loads(old.read_text())
    manifests={c:json.loads((Path('data/processed')/c/'feature_manifest.json').read_text()) for c in CITIES}
    feature_lists={c:[f for f in m['feature_names'] if f.startswith(('fab_','cop_','lc_')) and f.endswith('_cityrank') and not f.startswith(('lc_builtup','lc_intersection'))] for c,m in manifests.items()}
    trigger=json.loads(Path('models/rain_percentile_trigger.json').read_text())
    tide=json.loads(Path('models/m2_ho_chi_minh_tide.json').read_text())
    config={'version':1,'fit_selection':'dated records with date < --cutoff plus train_undated; filter split in train/train_undated before reading date; test_locked excluded',
      'model1':{'scorer':'lgbm_phys_cityrank','target':'ever_flood_rain; tide fit on HCMC only','features_by_city':feature_lists,'hyperparameters':{'n_estimators':160,'max_depth':4,'num_leaves':7,'learning_rate':.035,'reg_lambda':8.0,'reg_alpha':1.5,'min_child_samples':30,'subsample':.85,'colsample_bytree':.8,'subsample_freq':1,'deterministic':True,'force_col_wise':True,'n_jobs':2,'random_state':41073},'unlabeled_route_rule':'in-universe only; all labeled routes retained; fixed-seed subsample at most 20,000 unlabeled routes per city','seeds':{'rain_sampling':50723,'tide_sampling':81023,'lightgbm':41073}},
      'susceptibility_mapping':{'universe':'highway class in motorway/trunk/primary/secondary/tertiary/unclassified/residential/living_street and _link variants; length_m >= 30; service excluded','in_universe':'S_model=0.90 * (right-inclusive percentile rank within in-universe score distribution, divided by n+1)','out_of_universe':'half of corresponding within-universe score percentile, then 0.90 scale','history':'route with FIT history: 0.90 + 0.10*min(1,n_distinct_dates/3); otherwise 0','hybrid':'max(S_model,S_history)'},
      'rain_trigger':{'form':'pooled logistic regression on clipped logit of daily max-3h percentile and daily-total percentile','features':trigger['selected_features'],'C':trigger['C'],'class_weight':trigger['class_weight'],'random_state':trigger['random_state'],'fit_source':'ERA5 source/city-specific percentile CDF','live_test_source':'IFS source/city-specific percentile CDF; fallback to ERA5 percentile if IFS missing','refit_from_unlocked_fit_labels_for_cutoff':True,'current_fit_coefficients':{'coef':trigger['coef'],'intercept':trigger['intercept']},'label_free_baseline':'sigmoid((q_max3h-0.95)/0.02'},
      'rain_percentile_cdfs':{'HCMC':'ERA5 2002–2024, IFS 2017–2024, all calendar days','Da Nang':'ERA5 2002–2024, IFS 2017–2024, all calendar days'},
      'q_watch':trigger['states']['q_watch'],'q_alert':trigger['states']['q_alert'],'tide_trigger':{'kind':tide['kind'],'feature':tide.get('feature'),'parameters':tide,'fit':'Task 5 HCMC harmonic-tide percentile trigger; unchanged'},
      'tide_day_thresholds_by_city':{c:json.loads(Path('models/combination_thresholds.json').read_text())['thresholds'][c]['tide'] for c in CITIES},
      'levels':{'quiet':'T < q_watch','watch':'q_watch <= T < q_alert','alert':'T >= q_alert','route_A':'top 5% S_hyb in selected route scope','route_B':'next 15%','high':'alert and route A','medium':'alert and route B or watch and route A'},
      'continuous_route_day_score':'P=1-(1-S_rain*T_rain)*(1-S_tide*T_tide)','history_and_model':'locked holdout is not used in fit, CDF, threshold, or selection'}
    old.write_text(json.dumps(config,indent=2));return config

def write_model_card():
    text='''# Model card — flood-risk routes, pre-test freeze

## Models and data

Model 1 estimates persistent route susceptibility S with `lgbm_phys_cityrank`, using terrain, water proximity, and non-built-up land-cover city-rank features. It is fit on official IRD observations in HCMC and citizen reports in Da Nang, treating unlabeled routes as negatives with a fixed cap of 20,000 sampled routes/city. Route history is retained as a separate high-priority term.

The shared rain trigger is a regularized logistic model on city/source CDF percentiles for daily maximum 3-hour rain and daily total. Its coefficients are fit from pooled pre-2023 FIT days using ERA5 percentile inputs. Live/test input is IFS percentiles with ERA5 fallback. The tide trigger remains the earlier HCMC astronomical-tide percentile model; Da Nang has no tide labels.

## Evidence before the locked test

Model 1 transfer baseline: `lgbm_phys_cityrank` PRIMARY **0.331 [0.299, 0.371]**, HEADLINE **0.458 [0.421, 0.498]**. Exposure-only baseline PRIMARY **0.124 [0.094, 0.152]**, HEADLINE **0.219 [0.194, 0.263]**. Other baseline rankings and intervals are in `reports/m1_leaderboard.md`.

Shared percentile rain model selected max-3h + daily-total percentiles; leave-one-year-out mean AUC was **0.772** across nine estimable years. The fixed DEV trigger on IFS percentiles had AUC HCMC **0.705 [0.529, 0.870]** and Da Nang **0.758 [0.658, 0.856]**; rain shares and ERA5-input comparison are in `reports/percentile_trigger_dev.md`. The A4 FIT threshold target was not fully met: alert captured 57.1% of FIT flood days while 85.1% of rainy-season no-report days stayed quiet; watch-or-alert captured 85.7%.

On IFS-driven DEV, HCMC had 46 records / 6 days and Da Nang 126 / 16 days. In-universe D1 model/history/hybrid were HCMC **.203 [.067,.342] / .288 [.096,.583] / .217 [.067,.383]**, Da Nang **.210 [.076,.366] / .097 [0,.222] / .097 [0,.222]**. In-universe D2 top-5% hit rates model/history/hybrid were HCMC **.482/.288/.510**, Da Nang **.367/.097/.316**; at top-20% they were HCMC **.679/.288/.679**, Da Nang **.903/.097/.903**. Full paired intervals, NEW-route results, D3 alert burden, and D6 record capture are in `reports/dev_eval_ifs.md` and `reports/dev_eval_era5.md`.

The fixed hybrid exactly preserves history hit rate at K=history size. The requested model-floor check fails for Da Nang in-universe at 5% (hybrid-model hit-rate delta **−.051**); this is a real conflict between fixed history priority and the new-route ranking, not an interval artifact.

## Biases and limits

- HCMC IRD and press-style reporting overrepresent named major roads; road class had strong raw single-feature performance in earlier work.
- Da Nang citizen reports concentrate in dense residential areas and one FIT event (2022-10-14) dominates its early label history.
- ERA5 is coarse (~0.25°, about 28 km); IFS is nominally 9 km. The shared percentile mapping helps harmonize distributions but cannot create local storm detail.
- Tide is only empirically verifiable in HCMC; the Da Nang tide model has no positive labels.
- Unreported routes/days are not confirmed dry. The locked 2025+ set has not been accessed.

These data do not prove calibration, causal hydrologic susceptibility, operational lead-time skill, or generalization to the locked period. DEV is small, event-based, and affected by reporting practices. Section 7 metrics measure ranking/capture under the recorded label process, not flood probability truth.
'''
    Path('reports/model_card.md').write_text(text)

def final_trigger(cutoff,outdir):
    frames={c:pd.read_parquet(Path('data/processed/rain_percentiles')/f'{c}_era5.parquet').set_index('date') for c in CITIES}
    lab=rain_labels();data,cols,model,cv=fit_candidates(frames,lab,cutoff);states=choose_states(data,model,cols)
    fitcfg={'selected_features':cols,'C':.1,'class_weight':'balanced','random_state':713,'coef':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),'n_fit_rows':len(data),'n_fit_positive_days':int(data.positive.sum()),'fit_cutoff':cutoff,'max_fit_date':str(pd.Timestamp(cutoff)-pd.Timedelta(days=1)),'pooled_cities':list(CITIES),'fit_source':'ERA5 percentiles','cv':cv,'states':states}
    (outdir/'rain_trigger.json').write_text(json.dumps(fitcfg,indent=2))

def fit(cutoff,pilot=False,verify=False):
    parsed=pd.Timestamp(cutoff)
    if parsed != parsed.normalize() or len(cutoff)!=10:raise ValueError('--cutoff must be an ISO date')
    config=write_config();write_model_card();outdir=Path('models')/f'final_{cutoff}'
    if pilot:
        result=fit_route_models(pilot=True,save=False,cutoff=cutoff)
        print(json.dumps({'pilot':True,'cutoff':cutoff,'best_scorer':result[0].__name__ if hasattr(result[0],'__name__') else config['model1']['scorer'],'rows':{c:len(x) for c,x in result[2].items()}},default=str));return
    outdir.mkdir(parents=True,exist_ok=True)
    scorer,manifest,features,training,rain_model,tide_model=fit_route_models(pilot=False,save=False,cutoff=cutoff)
    rec=read_fit_records();rec=rec[rec.date.isna()|(rec.date<pd.Timestamp(cutoff))].copy();joined=join_matched_records(rec)
    for city,ft in features.items():
        ft=ft.reset_index(drop=True);routes=ft.route_id.astype(str).to_numpy();uni=ft.in_universe.to_numpy(bool)
        smr=.9*percentile_score(scorer.predict(rain_model,ft),uni)
        smt=.9*percentile_score(scorer.predict(tide_model,ft),uni) if city=='ho_chi_minh' else np.zeros(len(ft),np.float32)
        hist=history_scores(joined,city,routes,cutoff=cutoff);shr=np.maximum(smr,hist['rain'][0]);sht=np.maximum(smt,hist['tide'][0])
        out=ft[['route_id','in_universe']].copy()
        for col,val in [('S_rain',smr),('S_tide',smt),('S_hyb_rain',shr),('S_hyb_tide',sht),('S_hist_rain',hist['rain'][0]),('S_hist_tide',hist['tide'][0]),('H_rain',hist['rain'][1].astype(np.uint8)),('H_tide',hist['tide'][1].astype(np.uint8)),('H_any',(hist['rain'][1]|hist['tide'][1]).astype(np.uint8)),('n_distinct_dates_rain',hist['rain'][2].astype(np.uint16)),('n_distinct_dates_tide',hist['tide'][2].astype(np.uint16))]:out[col]=val
        citydir=outdir/city;citydir.mkdir(parents=True,exist_ok=True);out.to_parquet(citydir/'route_susceptibility.parquet',index=False)
    for name,bundle in [('rain',rain_model),('tide',tide_model)]:
        if bundle is not None:bundle['model'].booster_.save_model(str(outdir/f'm1_s_{name}.txt'))
    final_trigger(cutoff,outdir)
    (outdir/'final_config.json').write_text(json.dumps(config,indent=2))
    metadata={'cutoff':cutoff,'max_training_date':str(pd.Timestamp(cutoff)-pd.Timedelta(days=1)),'route_fit_split':'train and train_undated; date < cutoff','test_locked_read':False,'scorer':config['model1']['scorer'],'rain_unlabeled_cap_per_city':20000}
    (outdir/'fit_metadata.json').write_text(json.dumps(metadata,indent=2))
    for city in CITIES:
        if cutoff=='2023-01-01':
            base=pd.read_parquet(Path('data/processed')/city/'route_susceptibility.parquet').sort_values('route_id').reset_index(drop=True)
            got=pd.read_parquet(outdir/city/'route_susceptibility.parquet').sort_values('route_id').reset_index(drop=True)
            cols=['route_id','in_universe','S_rain','S_tide','S_hyb_rain','S_hyb_tide','H_rain','H_tide','H_any']
            if len(base)!=len(got) or not np.allclose(base[['S_rain','S_tide','S_hyb_rain','S_hyb_tide']].to_numpy(float),got[['S_rain','S_tide','S_hyb_rain','S_hyb_tide']].to_numpy(float),atol=1e-7,rtol=0):raise AssertionError(f'{city}: final cutoff route scores differ from Part B')
            if not base[cols].drop(columns=['S_rain','S_tide','S_hyb_rain','S_hyb_tide']).equals(got[cols].drop(columns=['S_rain','S_tide','S_hyb_rain','S_hyb_tide'])):raise AssertionError(f'{city}: final cutoff history/universe mismatch')
    del scorer,manifest,features,training,rain_model,tide_model,joined,rec;gc.collect()
    if verify and cutoff=='2023-01-01':
        for source in ('era5','ifs'):
            tag='final_2023_'+source
            cmd=[sys.executable,'scripts/eval_dev.py','--rain-source',source,'--artifact-dir',str(outdir),'--output-tag',tag]
            env=os.environ.copy();env.update({'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2','PYTHONPATH':'src'})
            subprocess.run(cmd,check=True,env=env)
            old=pd.read_csv(f'reports/dev_results_{source}.tsv',sep='\t',dtype=str).fillna('');new=pd.read_csv(f'reports/dev_results_{tag}.tsv',sep='\t',dtype=str).fillna('')
            if not old.equals(new):raise AssertionError(f'{source} DEV results differ from Part B')
    print(json.dumps({'cutoff':cutoff,'artifact_dir':str(outdir),'verified_exact_DEV':bool(verify and cutoff=='2023-01-01')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cutoff',required=True);p.add_argument('--pilot',action='store_true');p.add_argument('--verify-dev',action='store_true');a=p.parse_args();fit(a.cutoff,a.pilot,a.verify_dev)

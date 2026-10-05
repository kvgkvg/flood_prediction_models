import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from floodrisk.evalm1 import metric_values, bootstrap_metrics, scorer_input, validate_scorer_frame, headline_bootstrap_difference, _prop_metrics

def _toy():
    h=np.repeat(['primary','tertiary','residential'],100)
    y=np.zeros(300,dtype=bool); y[[*range(10),100,101,200]]=True
    rank=np.repeat([3.,2.,1.],100)
    return h,y,rank

def test_class_only_scorer_is_controlled_within_road_group():
    h,y,s=_toy();m=metric_values(y,s,h,np.linspace(0,1,len(y)))
    assert .07 <= m['strat_recall_at_10'] <= .13
    assert m['recall_at_10'] > .1

def test_perfect_scorer_captures_all_positives():
    h,y,_=_toy();m=metric_values(y,y.astype(float),h,np.linspace(0,1,len(y)))
    assert m['recall_at_10']==pytest.approx(1.)
    assert m['strat_recall_at_10']==pytest.approx(1.)

def test_propensity_only_scorer_is_near_ten_percent_within_strata():
    n=1000; y=np.tile([True,False],n//2); propensity=np.repeat(np.linspace(.01,.99,10),100)
    p,_,_=_prop_metrics(y,propensity,propensity,np.ones(n,bool),draws=20,seed=9)
    assert .07 <= p['prop_recall_at_10'] <= .13

def test_scorer_frame_removes_identifiers_and_labels_on_predict():
    f=pd.DataFrame({'route_id':['a','b'],'city':['x','x'],'geometry':[None,None],'highway_class':['primary','secondary'],'road_highway_class':['primary','secondary'],'x':[1.,2.],'ever_flood_rain':[True,False],'n_records':[1.,np.nan]})
    tr=scorer_input(f,'ever_flood_rain',True);te=scorer_input(f,'ever_flood_rain',False)
    assert set(tr.columns)=={'road_highway_class','label','sample_weight'}
    assert set(te.columns)=={'road_highway_class'}
    validate_scorer_frame(tr);validate_scorer_frame(te)

def test_bootstrap_metric_intervals_are_finite():
    h,y,s=_toy();point,ci,_=bootstrap_metrics(y,s,h,np.linspace(0,1,len(y)),draws=30,seed=7)
    assert 0<=ci['strat_recall_at_10'][0]<=ci['strat_recall_at_10'][1]<=1
    assert 0<=point['recall_at_10']<=1

def test_paired_headline_comparison_is_zero_for_identical_predictions():
    h,y,s=_toy();pred=pd.DataFrame({'route_id':[str(i) for i in range(len(y))],'score':s,'label':y,'highway_class':h,'lc_builtup_500m_frac':np.linspace(0,1,len(y))})
    a={'predictions':{t:pred for t in ('T1','T2','T3')}};b={'predictions':{t:pred.copy() for t in ('T1','T2','T3')}}
    mean,ci,p=headline_bootstrap_difference(a,b,draws=25,seed=4)
    assert mean==pytest.approx(0);assert ci==pytest.approx([0,0]);assert p==0

def test_frozen_eval_harness_sha256():
    hashes=json.loads(Path('tests/frozen_hashes.json').read_text())
    path=Path('src/floodrisk/evalm1.py')
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    assert hashes['src/floodrisk/evalm1.py']==actual, 'frozen evaluation harness changed; only orchestrator may approve updating tests/frozen_hashes.json'

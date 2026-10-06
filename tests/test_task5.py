import json
from pathlib import Path
import numpy as np
import pandas as pd

from floodrisk.drivers import _cell_daily
from floodrisk.combine import (route_trigger, route_bands, levels_from_bands,
    history_scores, percentile_score)


def test_rain_daily_rolling_stops_at_local_midnight_and_uses_local_dates():
    # UTC+7 input makes the local calendar boundary explicit.
    idx=pd.date_range('2024-01-01 00:00',periods=54,freq='h',tz='Asia/Ho_Chi_Minh')
    rain=np.ones(len(idx),dtype=float)
    rain[22:24]=20.0
    rain[24:26]=100.0
    got=_cell_daily(pd.DataFrame({'time':idx,'precipitation':rain}),10.8,106.7).set_index('date')
    assert pd.Timestamp('2024-01-01') in got.index
    assert pd.Timestamp('2024-01-02') in got.index
    # Day two's max-three-hour sum is three hours within day two; no previous
    # evening rain can enter it.  Day two's antecedent total is day one's 24 h.
    assert got.loc[pd.Timestamp('2024-01-02'),'rain_max_3h_mm']==201.0
    assert got.loc[pd.Timestamp('2024-01-02'),'rain_prev_24h_mm']==62.0


def test_p_formula_and_hybrid_history_floor():
    p=route_trigger([.2,.8],[.1,.3],.5,.4)
    expected=1-(1-np.array([.2,.8])*.5)*(1-np.array([.1,.3])*.4)
    assert np.allclose(p,expected,atol=1e-6)
    model=np.array([.2,.8]);hist=np.array([.9,.0]);hyb=np.maximum(model,hist)
    assert np.all(hyb>=model) and np.all(hyb>=hist)


def test_day_and_route_states_follow_explicit_rules():
    bands=np.array([2,1,0],np.uint8);th={'rain':{'t_lo':.3,'t_hi':.7},'tide':{'t_lo':.3,'t_hi':.7}}
    assert levels_from_bands(bands,np.zeros(3,np.uint8),.8,0.,th).tolist()==[2,1,0]
    assert levels_from_bands(bands,np.zeros(3,np.uint8),.5,0.,th).tolist()==[1,0,0]


def test_out_of_universe_percentile_is_halved():
    score=percentile_score([.1,.2,.3],[True,True,False])
    assert 0<=score[0]<1 and 0<=score[1]<1 and score[2]<.5


def test_history_score_uses_fit_distinct_dates():
    j=pd.DataFrame({'city':['c']*4,'route_id':['a','a','a','b'],'date':pd.to_datetime(['2020-01-01','2020-02-01','2020-03-01',None]),'cause':['rain']*4})
    got=history_scores(j,'c',['a','b','z'])['rain'][0]
    assert np.allclose(got,[1.0,.9,0.0],atol=1e-7)


def test_hybrid_priority_keeps_every_history_route_above_unseen_model_scores():
    model=.9*np.array([.99,.92,.80,.40],np.float32)
    history=np.array([.9+.1/3,.9,.0,0.],np.float32)
    hybrid=np.maximum(model,history)
    # Two history routes: hybrid top-2 is exactly the history set; recurrence breaks ties.
    assert set(np.argsort(-hybrid)[:2])=={0,1}
    assert np.all(hybrid[:2]>=.9) and np.all(hybrid[2:]<.9)


def test_fitted_artifacts_have_pre_dev_cutoff_when_present():
    for path in Path('models').glob('*.json'):
        data=json.loads(path.read_text())
        date=data.get('max_training_date',data.get('max_fit_date'))
        if date:
            assert pd.Timestamp(date)<pd.Timestamp('2023-01-01'),path

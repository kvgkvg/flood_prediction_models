import json
from pathlib import Path
import numpy as np
import pandas as pd

from floodrisk.drivers import _cell_daily
from floodrisk.combine import route_trigger, levels


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
    p,ph=route_trigger([.2,.8],[.1,.3],.5,.4,[0,1],[0,0],.6)
    expected=1-(1-np.array([.2,.8])*.5)*(1-np.array([.1,.3])*.4)
    assert np.allclose(p,expected,atol=1e-6)
    assert ph[1]>=p[1]


def test_levels_are_monotone():
    v=levels(None,np.arange(100,dtype=np.float32))
    assert v['medium']<=v['high']


def test_fitted_artifacts_have_pre_dev_cutoff_when_present():
    for path in Path('models').glob('*.json'):
        data=json.loads(path.read_text())
        date=data.get('max_training_date',data.get('max_fit_date'))
        if date:
            assert pd.Timestamp(date)<pd.Timestamp('2023-01-01'),path

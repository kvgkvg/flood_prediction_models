from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

from floodrisk.evidence import update_probability,deduplicate_user_route,displayed_level

def test_evidence_odds_multipliers_and_decay():
    now=pd.Timestamp('2026-01-01T12:00:00Z')
    base=[{'user_id':'u1','route_id':'r','timestamp':now,'status':'flooded'}]
    assert np.isclose(update_probability(.5,base,now),.75)
    dry=[{'user_id':'u1','route_id':'r','timestamp':now,'status':'not_flooded'}]
    assert np.isclose(update_probability(.5,dry,now),.25)
    official=[{'user_id':'agency','route_id':'r','timestamp':now,'status':'flooded','provenance_class':'official_observation'}]
    assert np.isclose(update_probability(.5,official,now),10/11)
    aged=[{'user_id':'u1','route_id':'r','timestamp':now-pd.Timedelta(minutes=30),'status':'flooded'}]
    assert np.isclose(update_probability(.5,aged,now),np.sqrt(3)/(1+np.sqrt(3)))

def test_evidence_deduplicates_user_route_30_minutes_and_display_level():
    now=pd.Timestamp('2026-01-01T12:00:00Z')
    rows=[{'user_id':'u','route_id':'r','timestamp':now-pd.Timedelta(minutes=m),'status':'flooded','depth_cm':depth} for m,depth in [(40,5),(20,35),(0,5)]]
    assert len(deduplicate_user_route(rows))==2
    # Two light reports vs one high report, using deduplicated reports.
    assert displayed_level(rows,now)=='light'

def test_export_routes_schema_and_geometries():
    required={'route_id','name','highway_class','in_universe','geometry','lowest_segment','lowest_segment_unverified','S_hyb_rain','S_hyb_tide','route_state_rain','route_state_tide','has_history','n_history_dates','max_recorded_depth_cm','depth_class','depth_provenance','provenance'}
    for city in ('ho_chi_minh','da_nang'):
        p=Path('data/export')/city/'routes.parquet';assert p.exists()
        g=gpd.read_parquet(p);assert required.issubset(g.columns);assert g.crs.to_epsg()==4326
        assert len(g)>0 and g.route_id.notna().all() and g.lowest_segment_unverified.all()
        assert set(g.route_state_rain.dropna()).issubset({'A','B','C'})
        assert (Path('data/export')/city/'routes.geojson.gz').exists()

def test_hourly_offline_samples_have_three_horizons_and_no_network():
    required={'route_id','valid_time','horizon_h','P','level','S_rain','S_tide','T_rain','T_tide','day_state_rain','day_state_tide','provenance','active_report_count','max_recorded_depth_cm'}
    for city in ('ho_chi_minh','da_nang'):
        out=Path('data/export')/city
        p=out/'risk_hourly.parquet';assert p.exists()
        d=pd.read_parquet(p);assert required.issubset(d.columns)
        assert set(d.horizon_h.unique())=={0,1,2};assert d.P.between(0,1).all();assert set(d.level.unique()).issubset({'low','medium','high'})
        status=pd.read_json(out/'city_status.json',typ='series');assert bool(status.offline_sample)

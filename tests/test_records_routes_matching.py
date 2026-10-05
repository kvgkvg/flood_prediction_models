import numpy as np
import geopandas as gpd
import pandas as pd
import pytest
import sys
from pathlib import Path
from shapely.geometry import LineString, Point
from floodrisk.records import normalize_name, stable_route_id, build_route_labels, _split
from floodrisk.matching import match_records
from floodrisk.terrain import fill_depressions,relative_elevation,d8_flow_accumulation
from floodrisk.features import validate_feature_columns, add_city_ranks
sys.path.insert(0,str(Path('scripts').resolve()))
from download_rain import request_points, weight

def test_name_normalisation():
    assert normalize_name('Đường Nguyễn Huệ') == 'nguyen hue'
    assert normalize_name(' PHỐ   Trần Hưng Đạo ') == 'tran hung dao'

def test_rain_grid_and_weight_are_native_era5():
    points=request_points((106.436,10.55,107.0,11.05),'era5')
    assert len(points)==9
    assert len(set(points))==len(points)
    assert all(abs(x*4-round(x*4))<1e-8 and abs(y*4-round(y*4))<1e-8 for y,x in points)
    assert weight(pd.Timestamp('2024-01-01').date(),pd.Timestamp('2024-01-14').date())==1
    assert weight(pd.Timestamp('2024-01-01').date(),pd.Timestamp('2024-01-15').date())==2

def test_route_id_is_stable():
    x=stable_route_id('ho_chi_minh','ward-1','nguyen hue',True,['1','2'])
    assert x==stable_route_id('ho_chi_minh','ward-1','nguyen hue',True,['9'])
    assert x!=stable_route_id('ho_chi_minh','ward-2','nguyen hue',True,['1'])
    assert stable_route_id('da_nang','ward','',False,['10','2'])==stable_route_id('da_nang','ward','',False,['2','10'])

def test_ird_year_fallback_split():
    assert _split(pd.NaT,2025)=='test_locked_undated'
    assert _split(pd.NaT,2026.0)=='test_locked_undated'
    assert _split(pd.NaT,2024)=='train_undated'
    assert _split(pd.NaT,None)=='train_undated'

def test_terrain_bowl_and_flow():
    bowl=np.full((5,5),10,dtype=np.float32);bowl[2,2]=0
    filled=fill_depressions(bowl)
    assert filled[2,2]>bowl[2,2]
    assert (filled-bowl)[2,2]>0
    assert relative_elevation(bowl,np.full_like(bowl,9))[2,2]<0
    slope=np.array([[9,8,7],[8,7,6],[7,6,5]],dtype=np.float32)
    acc=d8_flow_accumulation(slope)
    assert acc[2,2]>acc[0,0]

def test_forbidden_feature_columns_and_cityrank_bounds():
    validate_feature_columns(['route_id','fab_elevation_mean','road_highway_rank_cityrank'])
    try:validate_feature_columns(['route_id','lat'])
    except ValueError:pass
    else:raise AssertionError('lat must be forbidden')
    df=add_city_ranks(pd.DataFrame({'in_universe':[True,True,False],'elev':[2.,1.,99.]}),['elev'])
    assert df.elev_cityrank.dropna().between(0,1).all()
    assert pd.isna(df.elev_cityrank.iloc[2])

@pytest.mark.parametrize('city',['ho_chi_minh','da_nang'])
def test_built_feature_tables_are_label_free_and_cityranks_bounded(city):
    path=Path('data/processed')/city/'route_features.parquet'
    if not path.exists():pytest.skip('route feature parquet not built yet')
    f=pd.read_parquet(path)
    assert f.route_id.is_unique
    validate_feature_columns(f.columns)
    ranks=[c for c in f if c.endswith('_cityrank')]
    for c in ranks:
        x=f[c].dropna()
        assert x.between(0,1).all(),c

def test_ird_projection_sanity_pre_holdout():
    p='data/raw/ird_hcmc/HCMC_Floods_BDD.gpkg'
    src=gpd.read_file(p,layer='Flood_event_locations')
    dates=pd.to_datetime(src.Date,errors='coerce')
    src=src.loc[dates.dt.year.lt(2025)].to_crs(4326)
    assert len(src)>0
    w,s,e,n=(106.4363502282,10.55,107.0,11.05)
    assert src.geometry.x.between(w,e).all()
    assert src.geometry.y.between(s,n).all()

def test_matcher_tiny_named_road():
    routes=gpd.GeoDataFrame([{'route_id':'r1','name':'Đường Nguyễn Huệ','name_norm':'nguyen hue','named':True,'geometry':LineString([(106.7,10.8),(106.701,10.8)])}],crs=4326)
    records=gpd.GeoDataFrame([{'record_id':'x','city':'ho_chi_minh','lat':10.8,'lon':106.7005,'location_precision':'street','road_name_text':'Nguyen Hue','split':'train','geometry':Point(106.7005,10.8)}],crs=4326)
    out=match_records(records,{'ho_chi_minh':routes})
    assert out.iloc[0].route_id=='r1'
    assert out.iloc[0].match_type=='name+distance'

def test_labels_ignore_locked_rows():
    base=pd.DataFrame([{'record_id':'a','city':'da_nang','route_id':'r1','split':'train','date':pd.Timestamp('2022-10-14').date(),'cause':'rain','depth_cm':20}])
    locked=pd.DataFrame([{'record_id':'z','city':'da_nang','route_id':'r2','split':'test_locked','date':pd.Timestamp('2025-01-01').date(),'cause':'combined','depth_cm':999999}, {'record_id':'z2','city':'da_nang','route_id':'r3','split':'test_locked_undated','date':None,'cause':'combined','depth_cm':999999}])
    a=build_route_labels(base);b=build_route_labels(pd.concat([base,locked],ignore_index=True))
    pd.testing.assert_frame_equal(a,b)

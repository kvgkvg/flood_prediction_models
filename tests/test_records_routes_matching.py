import geopandas as gpd
import pandas as pd
import sys
from pathlib import Path
from shapely.geometry import LineString, Point
from floodrisk.records import normalize_name, stable_route_id, build_route_labels
from floodrisk.matching import match_records
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
    locked=pd.DataFrame([{'record_id':'z','city':'da_nang','route_id':'r2','split':'test_locked','date':pd.Timestamp('2025-01-01').date(),'cause':'combined','depth_cm':999999}])
    a=build_route_labels(base);b=build_route_labels(pd.concat([base,locked],ignore_index=True))
    pd.testing.assert_frame_equal(a,b)

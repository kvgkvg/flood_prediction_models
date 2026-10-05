from pathlib import Path
import json
import pandas as pd
import pytest
import rasterio

BBOX_FILE=Path('data/raw/osm/city_bboxes.json')

def test_city_bbox_file_and_sanity():
    assert BBOX_FILE.exists()
    data=json.loads(BBOX_FILE.read_text())
    assert set(data)=={'ho_chi_minh','da_nang'}
    for item in data.values():
        west,south,east,north=item['bbox']
        assert -180 <= west < east <= 180
        assert -90 <= south < north <= 90
        assert item['buffer_m']==2000

def test_expected_source_files_exist_and_are_readable():
    expected=[Path('data/raw/ird_hcmc/HCMC_Floods_BDD.gpkg'),Path('data/raw/uhslc_vung_tau/uhslc_vung_tau_hourly.csv')]
    assert all(p.exists() and p.stat().st_size>0 for p in expected)
    for city in ('ho_chi_minh','da_nang'):
        with rasterio.open(f'data/interim/dem/{city}_copernicus_glo30.tif') as ds: assert ds.count>=1
        assert list(Path('data/interim/landcover').glob(f'{city}_*.tif'))
        assert Path(f'data/raw/osm/{city}_features.gpkg').exists()
    assert list(Path('data/raw/open_meteo').rglob('*.parquet'))

def test_rasters_cover_city_bboxes():
    assert BBOX_FILE.exists()
    bboxes=json.loads(BBOX_FILE.read_text())
    for city in ('ho_chi_minh','da_nang'):
        files=list(Path('data/interim/dem').glob(f'{city}_*.tif'))
        assert files, f'missing DEM for {city}'
        west,south,east,north=bboxes[city]['bbox']
        with rasterio.open(files[0]) as ds:
            b=ds.bounds
            assert b.left<=west and b.bottom<=south and b.right>=east and b.top>=north

def test_rain_parquet_has_no_gaps_over_24h():
    files=list(Path('data/raw/open_meteo').rglob('*.parquet'))
    assert files
    by_point={}
    for file in files:
        df=pd.read_parquet(file,columns=['time'])
        if df.empty: continue
        point=file.parent.name
        by_point.setdefault(point,[]).extend(pd.to_datetime(df.time).tolist())
    for point,times in by_point.items():
        times=sorted(set(times))
        if len(times)>1:
            gaps=pd.Series(times).diff().dropna()
            assert gaps.max()<=pd.Timedelta(hours=24), f'{point} has gap {gaps.max()}'

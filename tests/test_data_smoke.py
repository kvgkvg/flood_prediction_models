from pathlib import Path
import json
import pandas as pd
import pytest
import rasterio
import geopandas as gpd
import pyarrow.parquet as pq
from floodrisk.cities import CITIES

BBOX_FILE=Path('data/raw/osm/city_bboxes.json')

def test_city_bbox_file_and_sanity():
    assert BBOX_FILE.exists()
    data=json.loads(BBOX_FILE.read_text())
    assert set(data)=={'ho_chi_minh','da_nang'}
    for slug,item in data.items():
        assert tuple(item['bbox'])==CITIES[slug].bbox
        west,south,east,north=item['bbox']
        assert -180 <= west < east <= 180
        assert -90 <= south < north <= 90
        assert len(item['admin_bbox'])==4
        if slug=='ho_chi_minh':
            assert west>=106.35 and east<=107.00 and south>=10.55 and north<=11.05
        else:
            assert west <108.05 and south <15.93 and east>=108.35 and north>16.16

def test_expected_source_files_exist_and_are_readable():
    expected=[Path('data/raw/ird_hcmc/HCMC_Floods_BDD.gpkg'),Path('data/raw/uhslc_vung_tau/uhslc_vung_tau_hourly.csv')]
    assert all(p.exists() and p.stat().st_size>0 for p in expected)
    for city in ('ho_chi_minh','da_nang'):
        with rasterio.open(f'data/interim/dem/{city}_copernicus_glo30.tif') as ds: assert ds.count>=1
        # Each land-cover crop must be readable as a raster.
        cover=list(Path('data/interim/landcover').glob(f'{city}_*.tif'))
        assert cover
        with rasterio.open(cover[0]) as ds: assert ds.count>=1
        for layer in ('roads','waterways_water','admin_boundaries'):
            path=Path(f'data/raw/osm/{city}/{layer}.gpkg')
            assert path.exists() and path.stat().st_size>0
            assert gpd.read_file(path,layer=layer).crs is not None
    assert Path('data/raw/danang_portal/flood_reports.parquet').exists()
    assert pq.read_metadata('data/raw/danang_portal/flood_reports.parquet').num_rows>0

def test_rasters_cover_city_bboxes():
    assert BBOX_FILE.exists()
    bboxes=json.loads(BBOX_FILE.read_text())
    for city in ('ho_chi_minh','da_nang'):
        files=list(Path('data/interim/dem').glob(f'{city}_*.tif'))
        assert files, f'missing DEM for {city}'
        west,south,east,north=bboxes[city]['bbox']
        for raster in files:
            with rasterio.open(raster) as ds:
                b=ds.bounds
                assert b.left<=west and b.bottom<=south and b.right>=east and b.top>=north, f'{raster} does not cover bbox: {b}'
        for raster in Path('data/interim/landcover').glob(f'{city}_*.tif'):
            with rasterio.open(raster) as ds:
                b=ds.bounds
                assert b.left<=west and b.bottom<=south and b.right>=east and b.top>=north, f'{raster} does not cover bbox: {b}'

@pytest.mark.skipif(not list(Path('data/raw/open_meteo').rglob('*.parquet')), reason='Open-Meteo quota is exhausted; downloader is ready but no valid ERA5 cache exists yet')
def test_rain_parquet_has_no_gaps_over_24h():
    files=list(Path('data/raw/open_meteo').rglob('*.parquet'))
    assert files
    by_point={}
    for file in files:
        df=pd.read_parquet(file,columns=['time','precipitation'])
        if df.empty: continue
        assert df['precipitation'].notna().any(), f'{file} contains no precipitation values'
        point=file.stem
        by_point.setdefault(point,[]).extend(pd.to_datetime(df.time).tolist())
    for point,times in by_point.items():
        times=sorted(set(times))
        if len(times)>1:
            gaps=pd.Series(times).diff().dropna()
            assert gaps.max()<=pd.Timedelta(hours=24), f'{point} has gap {gaps.max()}'

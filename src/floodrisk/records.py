"""Canonical flood observation records and training-only route labels."""
from __future__ import annotations
import hashlib, re, unicodedata
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from floodrisk.cities import CITIES

RECORD_COLUMNS=['record_id','city','lat','lon','geometry','location_precision','location_precision_raw','location_method_raw','date','time','flooded','depth_cm','depth_class','cause','cause_assumed','source','provenance_class','evidence_url','road_name_text','road_name_text_raw','split']

def normalize_name(value):
    s=str(value or '').replace('Đ','D').replace('đ','d').casefold()
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    s=re.sub(r'[^a-z0-9 ]',' ',s); s=' '.join(s.split())
    return re.sub(r'^(duong|pho)\s+','',s).strip()

def depth_group(value):
    try: x=float(value)
    except (TypeError,ValueError): return 'unknown'
    if pd.isna(x): return 'unknown'
    if x<10: return '<10'
    if x<=30: return '10-30'
    return '>30'

def _precision(location_type,method,raw):
    s=' '.join(str(x or '').strip().casefold() for x in (location_type,method,raw))
    if 'segment' in s or 'line' in s: return 'segment'
    if 'street' in s or 'road' in s: return 'street'
    if any(k in s for k in ('area','ward','district','commune','polygon')): return 'area'
    if any(k in s for k in ('point','high','medium','low')): return 'point'
    return 'unknown'

def _split(d, year=None):
    if not pd.isna(d):
        return 'test_locked' if pd.Timestamp(d).date().isoformat()>='2025-01-01' else 'train'
    try: y=int(float(year))
    except (TypeError,ValueError): y=None
    if y is not None and y>=2025:return 'test_locked_undated'
    return 'train_undated'

def _cause(v):
    s=str(v or '').strip().casefold()
    if 'combined' in s or 'both' in s: return 'combined'
    if 'rain' in s: return 'rain'
    if 'tide' in s: return 'tide'
    return 'unknown'

def parse_road_name(raw,city):
    if raw is None or pd.isna(raw): return None
    text=str(raw).strip()
    if city=='da_nang':
        text=text.split(',')[0].strip()
        text=re.sub(r'^(?:số\s*)?\d+[a-zA-Z]?\s+','',text,flags=re.I)
    return text or None

def build_records(root=Path('.')):
    rows=[]
    p=root/'data/raw/ird_hcmc/HCMC_Floods_BDD.gpkg'
    if p.exists():
        g=gpd.read_file(p,layer='Flood_event_locations').to_crs(4326)
        bbox=CITIES['ho_chi_minh'].bbox
        for rownum,r in enumerate(g.itertuples(index=False),start=1):
            d=pd.to_datetime(r.Date,errors='coerce'); geom=r.geometry
            if geom is None or geom.is_empty: continue
            lon,lat=geom.x,geom.y
            splitv=_split(d,r.Year)
            # Preserve the source point when the hard bbox clamp excludes it;
            # changing its position or dropping the event would corrupt evidence.
            dep=pd.to_numeric(pd.Series([r.Water_height_max_cm]),errors='coerce').iloc[0]
            cause=_cause(r.Cause)
            rawtext=r.Location_name
            precision=_precision(r.Location_type,r.Geocoding_method,r.Spatial_precision)
            rows.append(dict(record_id=f'ird:{r.Obs_id}:{rownum}',city='ho_chi_minh',lat=lat,lon=lon,geometry=geom,location_precision=precision,location_precision_raw=r.Spatial_precision,location_method_raw=r.Geocoding_method,date=d.date() if not pd.isna(d) else None,time=None,flooded=True,depth_cm=dep,depth_class=depth_group(dep),cause=cause,cause_assumed=False,source='IRD Dataverse doi:10.23708/8Y16HU',provenance_class='official_observation',evidence_url='https://dataverse.ird.fr/dataset.xhtml?persistentId=doi:10.23708/8Y16HU',road_name_text=rawtext,road_name_text_raw=rawtext,split=splitv))
    p=root/'data/raw/danang_portal/flood_reports.parquet'
    if p.exists():
        df=pd.read_parquet(p)
        for rownum,r in enumerate(df.itertuples(index=False),start=1):
            if pd.isna(r.lat) or pd.isna(r.lon): continue
            bbox=CITIES['da_nang'].bbox
            dt=pd.to_datetime(r.datetime,errors='coerce'); datev=dt.date() if not pd.isna(dt) else None; timev=dt.time().replace(tzinfo=None) if not pd.isna(dt) else None
            if _split(dt) != 'test_locked':
                assert bbox[0]-1e-5<=r.lon<=bbox[2]+1e-5 and bbox[1]-1e-5<=r.lat<=bbox[3]+1e-5, f'Da Nang pre-holdout point outside expanded urban bbox: {r.lon},{r.lat}'
            raw=r.address_road_text
            dep=pd.to_numeric(pd.Series([r.depth_cm]),errors='coerce').iloc[0]
            precise='street' if str(r.flood_type).casefold().strip()=='street' else ('point' if str(r.flood_type).casefold().strip()=='point' else 'unknown')
            rows.append(dict(record_id=f'danang:{r.id}:{rownum}',city='da_nang',lat=float(r.lat),lon=float(r.lon),geometry=Point(float(r.lon),float(r.lat)),location_precision=precise,location_precision_raw=r.flood_type,location_method_raw=None,date=datev,time=timev,flooded=True,depth_cm=dep,depth_class=depth_group(dep),cause='rain',cause_assumed=True,source='Da Nang flood portal',provenance_class='official_observation',evidence_url='https://muangap.danang.gov.vn/',road_name_text=parse_road_name(raw,'da_nang'),road_name_text_raw=raw,split=_split(dt)))
    frame=pd.DataFrame(rows,columns=RECORD_COLUMNS)
    if frame.record_id.duplicated().any(): raise ValueError('record_id values must be unique')
    return gpd.GeoDataFrame(frame,geometry='geometry',crs=4326)

def build_route_labels(records):
    df=records.loc[records.split.isin(['train','train_undated'])].copy()
    if 'route_id' not in df: raise ValueError('route_id must be joined before label aggregation')
    df=df.loc[df.route_id.notna()]
    def aggregate(g):
        dates=pd.to_datetime(g.loc[g.date.notna(),'date'],errors='coerce').dropna()
        causes=set(g.cause)
        return pd.Series({'n_records':len(g),'n_distinct_dates':dates.dt.date.nunique(),'ever_flood_rain':bool(causes & {'rain','combined'}),'ever_flood_tide':bool(causes & {'tide','combined'}),'max_depth_cm':pd.to_numeric(g.depth_cm,errors='coerce').max(),'first_date':dates.min().date() if len(dates) else None,'last_date':dates.max().date() if len(dates) else None})
    return df.groupby(['city','route_id'],sort=True).apply(aggregate,include_groups=False).reset_index()

def stable_route_id(city,ward,name_norm,named,component_ids=()):
    basis='|'.join([city,ward,name_norm if named else '', 'named' if named else ','.join(sorted(map(str,component_ids)))])
    return hashlib.sha1(basis.encode()).hexdigest()[:20]

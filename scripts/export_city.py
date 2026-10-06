#!/usr/bin/env python3
"""Export one city's frozen final route layer to GeoParquet and compressed GeoJSON."""
import argparse,gzip,json,math
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from shapely.geometry import LineString,MultiLineString,GeometryCollection,mapping
from shapely.ops import transform
from floodrisk.combine import route_bands

def _lines(g):
    if g is None or g.is_empty:return []
    if g.geom_type=='LineString':return [g]
    if g.geom_type=='MultiLineString':return list(g.geoms)
    if g.geom_type=='GeometryCollection':return [x for x in g.geoms if x.geom_type=='LineString']
    return []
def _sample_route(geom,src_crs,dataset):
    # Route coordinates already projected to the raster UTM CRS.
    points=[];owners=[]
    for k,line in enumerate(_lines(geom)):
        n=max(2,int(math.ceil(line.length/15))+1);dist=np.linspace(0,line.length,n);coords=[line.interpolate(float(x)).coords[0] for x in dist]
        points.extend(coords);owners.extend((k,float(x)) for x in dist)
    if not points:return geom
    vals=np.asarray([x[0] for x in dataset.sample(points)],float);ok=np.isfinite(vals)&(vals!=dataset.nodata)
    if not ok.any():return GeometryCollection()
    rank=np.flatnonzero(ok)[np.argsort(vals[ok])[:max(1,int(math.ceil(.2*ok.sum())))]]
    selected={int(i) for i in rank};pieces=[]
    byline={}
    for i,(k,d) in enumerate(owners):
        if i in selected:byline.setdefault(k,[]).append(d)
    lines=_lines(geom)
    for k,ds in byline.items():
        ds=sorted(ds);runs=[];run=[ds[0]]
        for x in ds[1:]:
            if x-run[-1]<=30.01:run.append(x)
            else:runs.append(run);run=[x]
        runs.append(run)
        for run in runs:
            line=lines[k]
            if len(run)==1:
                a=max(0,run[0]-7.5);b=min(line.length,run[0]+7.5)
                if a==b:continue
                pieces.append(LineString([line.interpolate(a),line.interpolate(b)]))
            else:pieces.append(LineString([line.interpolate(x) for x in run]))
    return MultiLineString(pieces) if pieces else GeometryCollection()

def _depth_class(v):
    if not np.isfinite(v):return 'unknown'
    return '<10' if v<10 else '10-30' if v<=30 else '>30'

def build(city,model_dir='models/final_2025-01-01',pilot=False):
    root=Path('data/processed')/city;out=Path('data/export')/city;out.mkdir(parents=True,exist_ok=True)
    routes=gpd.read_parquet(root/'routes.parquet',columns=['route_id','name','highway_class','in_universe','geometry'])
    if pilot:routes=routes.head(500).copy()
    sus=pd.read_parquet(Path(model_dir)/city/'route_susceptibility.parquet')
    attrs=routes.drop(columns='geometry').merge(sus,on=['route_id','in_universe'],how='left',validate='one_to_one')
    records=pd.read_parquet('data/processed/flood_records.parquet',columns=['record_id','city','date','depth_cm','depth_class','split'],filters=[('split','in',['train','train_undated'])])
    records=records[(records.city==city)&(records.date.isna()|(pd.to_datetime(records.date)<pd.Timestamp('2025-01-01')))]
    match=pd.read_parquet('data/processed/flood_record_matches.parquet',columns=['record_id','route_id'])
    labels=records.merge(match,on='record_id',how='inner').dropna(subset=['route_id'])
    depth=labels.groupby('route_id').agg(max_recorded_depth_cm=('depth_cm','max'),n_history_dates=('date','nunique')).reset_index()
    attrs=attrs.merge(depth,on='route_id',how='left');attrs['has_history']=attrs.H_any.fillna(0).astype(bool)
    attrs['n_history_dates']=attrs.n_history_dates.fillna(0).astype('int32');attrs['max_recorded_depth_cm']=attrs.max_recorded_depth_cm.astype(float)
    attrs['depth_class']=attrs.max_recorded_depth_cm.map(_depth_class);attrs['depth_provenance']=np.where(attrs.max_recorded_depth_cm.notna(),'official_observation',None)
    attrs['route_state_rain']=pd.Series(['C']*len(attrs),index=attrs.index);attrs['route_state_tide']=pd.Series(['C']*len(attrs),index=attrs.index)
    for score,col in [('S_hyb_rain','route_state_rain'),('S_hyb_tide','route_state_tide')]:
        bands=route_bands(attrs[score].fillna(0).to_numpy(),attrs[score].fillna(0).to_numpy(),np.ones(len(attrs),bool));attrs[col]=np.where(bands==2,'A',np.where(bands==1,'B','C'))
    centroid=routes.to_crs(4326).geometry.unary_union.centroid;zone=int(np.floor((centroid.x+180)/6))+1;metric=32600+zone;local=routes.to_crs(metric)
    raster=Path('data/interim/terrain')/city/'fabdem/elevation.tif'
    with rasterio.open(raster) as dem:
        segs=[_sample_route(g,dem.crs,dem) for g in local.geometry]
    simplified=local.geometry.simplify(2.0,preserve_topology=True)
    export=attrs.drop(columns=['H_any','H_rain','H_tide','n_distinct_dates_rain','n_distinct_dates_tide','S_hist_rain','S_hist_tide','S_rain','S_tide'],errors='ignore')
    export['lowest_segment_unverified']=True
    export['geometry']=simplified.to_crs(4326).values
    export['lowest_segment']=gpd.GeoSeries(segs,crs=metric).to_crs(4326).values
    export['provenance']=np.where(export.has_history,'official_observation','model_forecast')
    keep=['route_id','name','highway_class','in_universe','geometry','lowest_segment','lowest_segment_unverified','S_hyb_rain','S_hyb_tide','route_state_rain','route_state_tide','has_history','n_history_dates','max_recorded_depth_cm','depth_class','depth_provenance','provenance']
    export=export[keep]
    if pilot:
        print(f'pilot {city}: {len(export)} routes, {len(export.columns)} output fields; schema={export.columns.tolist()}');return export
    # Keep both geometry columns in GeoParquet; JSON stores the estimate as a nested geometry property.
    gdf=gpd.GeoDataFrame(export,geometry='geometry',crs=4326);gdf.to_parquet(out/'routes.parquet',index=False,compression='zstd')
    features=[]
    for row in gdf.itertuples(index=False):
        d=row._asdict();geom=d.pop('geometry');low=d.pop('lowest_segment');props={k:(v.item() if isinstance(v,np.generic) else v) for k,v in d.items()}
        if low is not None:props['lowest_segment']=mapping(low)
        features.append({'type':'Feature','geometry':mapping(geom),'properties':props})
    with gzip.open(out/'routes.geojson.gz','wt',encoding='utf-8') as f:json.dump({'type':'FeatureCollection','features':features},f,separators=(',',':'),default=str)
    print(json.dumps({'city':city,'routes':len(gdf),'parquet_bytes':(out/'routes.parquet').stat().st_size,'geojson_gz_bytes':(out/'routes.geojson.gz').stat().st_size,'pilot':False}))
    return gdf

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--city',required=True);p.add_argument('--model-dir',default='models/final_2025-01-01');p.add_argument('--pilot',action='store_true');a=p.parse_args();build(a.city,a.model_dir,a.pilot)

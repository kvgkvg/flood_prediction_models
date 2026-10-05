"""Label-free route feature extraction from terrain, land cover and OSM roads."""
from __future__ import annotations
import json, math
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling
from scipy.spatial import cKDTree
from pyproj import CRS

FORBIDDEN={'lat','lon','x','y','name','name_norm','ward_id','district_id','geometry'}
LANDCOVER={"builtup":{50},"tree":{10},"grass_shrub":{20,30},"cropland":{40},"bare":{60},"water":{80},"wetland_mangrove":{90,95}}
RASTERS=('elevation','focal_mean_300m','focal_min_300m','rel_elev_300m','focal_mean_1000m','focal_min_1000m','rel_elev_1000m','focal_mean_3000m','focal_min_3000m','rel_elev_3000m','elevation_percentile_1km','slope','fill_depth','flow_accumulation_log','twi','dist_water_any_m','hand_any_m','dist_water_major_m','hand_major_m')
CONTINUOUS=[]

def validate_feature_columns(columns):
    bad=FORBIDDEN.intersection(set(columns))
    if bad:raise ValueError(f'forbidden features: {sorted(bad)}')

def _samples(geom,step=15):
    geoms=list(geom.geoms) if geom.geom_type=='MultiLineString' else [geom]
    pts=[]
    for line in geoms:
        if line.is_empty or line.length==0:continue
        ds=np.arange(0,line.length,step);ds=np.append(ds,line.length)
        pts.extend(line.interpolate(float(d)) for d in ds)
    if not pts:return np.empty(0),np.empty(0)
    return np.fromiter((p.x for p in pts),dtype=float),np.fromiter((p.y for p in pts),dtype=float)

def _agg_values(v,key):
    v=np.asarray(v,dtype=float);v=v[np.isfinite(v)]
    if not len(v):return {}
    if key=='elevation':return {f'{key}_{s}':float(x) for s,x in zip(('min','p10','mean','max','range'),(v.min(),np.quantile(v,.1),v.mean(),v.max(),v.max()-v.min()))}
    if key=='fill_depth':return {f'{key}_{s}':float(x) for s,x in [('min',v.min()),('mean',v.mean()),('max',v.max())]} | {'fill_share_gt_0_2m':float((v>.2).mean())}
    if key.startswith('rel_elev'):return {f'{key}_{s}':float(x) for s,x in [('min',v.min()),('mean',v.mean())]}
    if key.startswith(('hand_','dist_water_')):return {f'{key}_{s}':float(x) for s,x in [('min',v.min()),('mean',v.mean())]}
    return {f'{key}_{s}':float(x) for s,x in [('mean',v.mean()),('max',v.max())]}

def _cityrank(df,continuous):
    mask=df.in_universe.fillna(False)
    for c in continuous:
        rank=pd.Series(np.nan,index=df.index,dtype=float)
        x=pd.to_numeric(df.loc[mask,c],errors='coerce')
        if x.notna().any():rank.loc[x.index]=x.rank(method='average',pct=True)
        df[c+'_cityrank']=rank.clip(0,1)
    return df

def add_city_ranks(df,continuous):
    mask=df.in_universe.fillna(False).astype(bool);ranked={}
    for c in continuous:
        ranked[c+'_cityrank']=pd.to_numeric(df.loc[mask,c],errors='coerce').rank(method='average',pct=True)
    out=pd.concat([df,pd.DataFrame(ranked,index=df.index)],axis=1)
    cols=list(ranked)
    if cols:out[cols]=out[cols].clip(0,1)
    return out

def build_features(city,root=Path('.')):
    rp=root/'data/processed'/city/'routes.parquet';routes=gpd.read_parquet(rp)
    zone=48 if city=='ho_chi_minh' else 49; crs=CRS.from_epsg(32600+zone)
    metric=routes.to_crs(crs).reset_index(drop=True)
    n=len(metric);rows=[{} for _ in range(n)]
    # Read raster stacks one DEM at a time so peak memory stays bounded.
    for dem,prefix in [('fabdem','fab_'),('copernicus','cop_')]:
        d=root/'data/interim/terrain'/city/dem
        names=[name for name in RASTERS if (d/f'{name}.tif').exists()]
        with rasterio.open(d/'elevation.tif') as ref:
            transform=ref.transform;shape=(ref.height,ref.width);raster_crs=ref.crs
        arrays={}
        for name in names:
            with rasterio.open(d/f'{name}.tif') as src:arrays[name]=(src.read(1),src.nodata)
        for i,geom in enumerate(metric.geometry):
            xs,ys=_samples(geom)
            if len(xs)==0:continue
            cols=np.floor((xs-transform.c)/transform.a).astype(int); rr=np.floor((ys-transform.f)/transform.e).astype(int)
            ok=(rr>=0)&(rr<shape[0])&(cols>=0)&(cols<shape[1]);rr=rr[ok];cols=cols[ok]
            for name,(a,nodata) in arrays.items():
                v=a[rr,cols].astype(float);v[(v==nodata)|(~np.isfinite(v))]=np.nan
                ag=_agg_values(v,name)
                rows[i].update({prefix+k:v for k,v in ag.items()})
        del arrays
    # WorldCover 10 m is reprojected to the matching 30 m grid. Buffer fractions
    # use an integral-image square-window proxy centered on each route midpoint.
    wc=root/'data/interim/landcover'/f'{city}_ESA_WorldCover_10m_2021_v200_Map.tif'
    if not wc.exists():
        matches=list((root/'data/interim/landcover').glob(f'{city}_*Map.tif'))
        if matches:wc=matches[0]
    elevpath=root/'data/interim/terrain'/city/'fabdem'/'elevation.tif'
    with rasterio.open(elevpath) as ref, rasterio.open(wc) as src:
        lc=np.zeros((ref.height,ref.width),dtype=np.uint8)
        reproject(src.read(1),lc,src_transform=src.transform,src_crs=src.crs,src_nodata=src.nodata,dst_transform=ref.transform,dst_crs=ref.crs,dst_nodata=0,resampling=Resampling.nearest)
        tr=ref.transform
    mids=np.asarray([[g.interpolate(.5,normalized=True).x,g.interpolate(.5,normalized=True).y] for g in metric.geometry])
    cx=np.floor((mids[:,0]-tr.c)/tr.a).astype(int);cy=np.floor((mids[:,1]-tr.f)/tr.e).astype(int)
    inside=(cx>=0)&(cy>=0)&(cx<lc.shape[1])&(cy<lc.shape[0]);lc_features={}
    for cl,classes in LANDCOVER.items():
        binary=np.isin(lc,list(classes)).astype(np.uint64); integ=np.pad(binary.cumsum(0).cumsum(1),((1,0),(1,0)))
        for radius in (200,500):
            rad=round(radius/30);x0=np.clip(cx-rad,0,lc.shape[1]);x1=np.clip(cx+rad+1,0,lc.shape[1]);y0=np.clip(cy-rad,0,lc.shape[0]);y1=np.clip(cy+rad+1,0,lc.shape[0])
            count=integ[y1,x1]-integ[y0,x1]-integ[y1,x0]+integ[y0,x0];area=np.maximum(1,(x1-x0)*(y1-y0));frac=count/area;frac[~inside]=np.nan
            lc_features[f'lc_{cl}_{radius}m_frac']=frac
    del lc
    # Road-neighbour summaries use route representative points and metric radius.
    coords=mids;tree=cKDTree(coords)
    lengths=metric.length.to_numpy(float)
    for i,p in enumerate(coords):
        ix=tree.query_ball_point(p,500); rows[i]['road_length_density_500m']=float(lengths[ix].sum()/(math.pi*500**2))
        rows[i]['road_intersections_300m']=max(0,len(tree.query_ball_point(p,300))-1)
    hw=routes.highway_class.fillna('unknown').astype(str)
    ranks={'motorway':8,'trunk':7,'primary':6,'secondary':5,'tertiary':4,'unclassified':3,'residential':2,'living_street':1,'service':0}
    base=pd.DataFrame({'route_id':routes.route_id,'in_universe':routes.in_universe.astype(bool),'road_highway_class':hw,'road_highway_rank':hw.map(ranks),'length_m':routes.length_m,'n_ways':routes.n_ways,'bridge_frac':routes.bridge_frac,'tunnel_frac':routes.tunnel_frac,'lanes':pd.to_numeric(routes.lanes,errors='coerce'),'named':routes.named.astype(bool)})
    feat=pd.concat([base,pd.DataFrame(rows),pd.DataFrame(lc_features)],axis=1)
    if 'fab_elevation_min' in feat:feat['fab_elev_min']=feat['fab_elevation_min']
    if 'fab_dist_water_any_m_min' in feat:feat['fab_dist_any_water_min']=feat['fab_dist_water_any_m_min']
    if feat.columns.duplicated().any():raise ValueError('duplicate feature columns')
    validate_feature_columns(feat.columns)
    categorical={'route_id','road_highway_class','named','in_universe'}
    continuous=[c for c in feat if c not in categorical and pd.api.types.is_numeric_dtype(feat[c])]
    feat=add_city_ranks(feat,continuous)
    target=root/'data/processed'/city;target.mkdir(parents=True,exist_ok=True);feat.to_parquet(target/'route_features.parquet',index=False)
    manifest={'city':city,'feature_count':len(feat.columns)-1,'feature_names':[c for c in feat if c!='route_id'],'groups':{}}
    for c in manifest['feature_names']:
        group='road'
        if c.startswith(('hand_','fab_hand_','cop_hand_','dist_water','fab_dist_water','cop_dist_water')):group='water'
        elif c.startswith('fab_'):group='terrain_fab'
        elif c.startswith('cop_'):group='terrain_cop'
        elif c.startswith('lc_'):group='landcover'
        elif c.startswith(('dist_water','hand_')):group='water'
        manifest['groups'][c]={'group':group,'description':c.replace('_',' ')}
    manifest['notes']=['Landcover buffer fractions approximate a route buffer by a square window around route midpoint on a 30 m grid.','Road density/intersection proxies count route representative points within the specified radius.']
    (target/'feature_manifest.json').write_text(json.dumps(manifest,indent=2))
    return feat,manifest

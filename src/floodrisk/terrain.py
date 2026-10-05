"""Small-city terrain derivatives on a 30 m UTM grid."""
from __future__ import annotations
from pathlib import Path
import heapq, math
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from scipy import ndimage as ndi
from pyproj import CRS
from floodrisk.cities import CITIES

NODATA=-9999.0

def relative_elevation(elevation, focal_mean):
    return np.asarray(elevation,dtype=np.float32)-np.asarray(focal_mean,dtype=np.float32)

def fill_depressions(elevation,valid=None):
    """Priority-Flood fill, seeded at raster edges and all nodata boundaries."""
    z=np.asarray(elevation,dtype=np.float32); valid=np.isfinite(z) if valid is None else np.asarray(valid,bool)&np.isfinite(z)
    h,w=z.shape; edge=np.zeros((h,w),bool)
    edge[0,:]=valid[0,:];edge[-1,:]=valid[-1,:];edge[:,0]|=valid[:,0];edge[:,-1]|=valid[:,-1]
    edge[1:,:]|=valid[1:,:]&~valid[:-1,:];edge[:-1,:]|=valid[:-1,:]&~valid[1:,:]
    edge[:,1:]|=valid[:,1:]&~valid[:,:-1];edge[:,:-1]|=valid[:,:-1]&~valid[:,1:]
    filled=z.copy(); seen=edge.copy(); ys,xs=np.nonzero(edge)
    heap=[(float(z[y,x]),int(y*w+x)) for y,x in zip(ys,xs)];heapq.heapify(heap)
    while heap:
        level,idx=heapq.heappop(heap); y,x=divmod(idx,w)
        for dy in (-1,0,1):
            ny=y+dy
            if ny<0 or ny>=h:continue
            for dx in (-1,0,1):
                if dx==0 and dy==0:continue
                nx=x+dx
                if nx<0 or nx>=w or seen[ny,nx] or not valid[ny,nx]:continue
                seen[ny,nx]=True; v=max(float(z[ny,nx]),level);filled[ny,nx]=v
                heapq.heappush(heap,(v,ny*w+nx))
    filled[~valid]=np.nan
    return filled

def d8_flow_accumulation(filled,valid=None,cell_size=30.0):
    """Single-direction D8 accumulation with deterministic routing over flats."""
    z=np.asarray(filled,dtype=np.float32);valid=np.isfinite(z) if valid is None else np.asarray(valid,bool)&np.isfinite(z)
    h,w=z.shape; dist_edge=ndi.distance_transform_edt(valid,sampling=cell_size).astype(np.float32)
    surface=z+dist_edge*1e-5; n=h*w; flat=surface.ravel(); mask=valid.ravel()
    target=np.full(n,-1,dtype=np.int64); best=np.zeros(n,dtype=np.float32)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if dx==dy==0:continue
            y0=max(0,-dy); y1=min(h,h-dy); x0=max(0,-dx); x1=min(w,w-dx)
            # Build row-strided indices without a full coordinate mesh.
            src=np.concatenate([np.arange(y*w+x0,y*w+x1,dtype=np.int64) for y in range(y0,y1)])
            dst=src+dy*w+dx; ok=mask[src]&mask[dst]
            src=src[ok];dst=dst[ok]
            slope=(flat[src]-flat[dst])/((math.sqrt(2) if dx and dy else 1)*cell_size)
            choose=(slope>best[src])&(slope>0)
            s=src[choose];target[s]=dst[choose];best[s]=slope[choose]
    ids=np.flatnonzero(mask);order=ids[np.argsort(flat[ids],kind='stable')[::-1]]
    acc=np.ones(n,dtype=np.float32)
    for start in range(0,len(order),65536):
        src=order[start:start+65536];dst=target[src];ok=dst>=0
        np.add.at(acc,dst[ok],acc[src[ok]])
    out=acc.reshape(h,w);out[~valid]=np.nan
    return out

def _write(path,array,profile):
    path.parent.mkdir(parents=True,exist_ok=True)
    a=np.asarray(array,dtype=np.float32);write=np.where(np.isfinite(a),a,NODATA).astype(np.float32)
    p=profile.copy();p.update(dtype='float32',count=1,nodata=NODATA,compress='deflate',predictor=3,tiled=True,blockxsize=256,blockysize=256)
    with rasterio.open(path,'w',**p) as dst:dst.write(write,1)

def _water_masks(city,shape,transform,crs):
    path=Path('data/raw/osm')/city/'waterways_water.gpkg';g=gpd.read_file(path).to_crs(crs)
    any_shapes=[];major_shapes=[];coast_shapes=[]
    for row in g.itertuples(index=False):
        geom=row.geometry
        if geom is None or geom.is_empty:continue
        ww='' if pd.isna(row.waterway) else str(row.waterway).strip().casefold()
        nat='' if pd.isna(row.natural) else str(row.natural).strip().casefold()
        ispoly=geom.geom_type in ('Polygon','MultiPolygon')
        waterpoly=ispoly and (nat=='water' or ww in ('riverbank','water'))
        waterline=(not ispoly) and bool(ww)
        if waterpoly or waterline:any_shapes.append((geom,1))
        if (waterpoly and geom.area>10000) or (waterline and ww in ('river','canal')):major_shapes.append((geom,1))
        if nat=='coastline' and geom.geom_type in ('LineString','MultiLineString'):coast_shapes.append((geom,1))
    def burn(shapes):
        return rasterize(shapes,out_shape=shape,transform=transform,fill=0,all_touched=True,dtype='uint8')>0 if shapes else np.zeros(shape,dtype=bool)
    return burn(any_shapes),burn(major_shapes),burn(coast_shapes)

def _local_percentile(elev,valid,size=67,bins=128):
    values=elev[valid]
    if not len(values):return np.full(elev.shape,np.nan,dtype=np.float32)
    lo=float(values.min());hi=float(values.max());out=np.full(elev.shape,np.nan,dtype=np.float32)
    denom=ndi.uniform_filter(valid.astype(np.float32),size=size,mode='constant',cval=0)
    if hi<=lo:out[valid]=0.5;return out
    scaled=np.zeros(elev.shape,dtype=np.float32)
    scaled[valid]=(elev[valid]-lo)/(hi-lo)*bins
    bi=np.clip(scaled.astype(np.int32),0,bins-1)
    for k in range(bins):
        m=valid&(bi==k)
        if not m.any():continue
        thresh=lo+(k+1)*(hi-lo)/bins
        cdf=ndi.uniform_filter(((elev<=thresh)&valid).astype(np.float32),size=size,mode='constant',cval=0)
        out[m]=np.clip(cdf[m]/np.maximum(denom[m],1e-9),0,1)
    return out

def build_terrain(city,dem,root=Path('.')):
    if city not in CITIES:raise ValueError(f'unknown city {city}')
    if dem not in ('fabdem','copernicus'):raise ValueError('dem must be fabdem or copernicus')
    srcpath=root/'data/interim/dem'/(f'{city}_fabdem_v1_2.tif' if dem=='fabdem' else f'{city}_copernicus_glo30.tif')
    if not srcpath.exists():raise FileNotFoundError(f'missing cropped DEM {srcpath}; run scripts/crop_fabdem_cached.py for FABDEM')
    bbox=CITIES[city].bbox; zone=int((((bbox[0]+bbox[2])/2)+180)//6)+1; epsg=32600+zone
    dstcrs=CRS.from_epsg(epsg);left,bottom,right,top=transform_bounds('EPSG:4326',dstcrs,*bbox,densify_pts=21)
    res=30.;width=math.ceil((right-left)/res);height=math.ceil((top-bottom)/res);transform=from_origin(left,top,res,res)
    elev=np.full((height,width),NODATA,dtype=np.float32);mask_src=np.zeros((height,width),dtype=np.uint8)
    with rasterio.open(srcpath) as src:
        reproject(source=rasterio.band(src,1),destination=elev,src_transform=src.transform,src_crs=src.crs,src_nodata=src.nodata,dst_transform=transform,dst_crs=dstcrs,dst_nodata=NODATA,resampling=Resampling.bilinear)
        # The source mask is authoritative even where a driver has no numeric nodata tag.
        source_mask=src.dataset_mask().astype(np.uint8)
        reproject(source=source_mask,destination=mask_src,src_transform=src.transform,src_crs=src.crs,dst_transform=transform,dst_crs=dstcrs,resampling=Resampling.nearest)
    valid=(mask_src>0)&(elev!=NODATA)&np.isfinite(elev)
    elev[~valid]=np.nan
    outdir=root/'data/interim/terrain'/city/dem;profile={'driver':'GTiff','height':height,'width':width,'count':1,'dtype':'float32','crs':dstcrs,'transform':transform,'nodata':NODATA}
    _write(outdir/'elevation.tif',elev,profile)
    for radius in (300,1000,3000):
        size=2*round(radius/res)+1
        denom=ndi.uniform_filter(valid.astype(np.float32),size=size,mode='constant',cval=0)
        sums=ndi.uniform_filter(np.where(valid,elev,0).astype(np.float32),size=size,mode='constant',cval=0)
        mean=sums/np.maximum(denom,1e-9);mean[~valid]=np.nan
        mn=ndi.minimum_filter(np.where(valid,elev,np.inf),size=size,mode='constant',cval=np.inf).astype(np.float32);mn[~valid|~np.isfinite(mn)]=np.nan
        _write(outdir/f'focal_mean_{radius}m.tif',mean,profile);_write(outdir/f'focal_min_{radius}m.tif',mn,profile)
        if radius in (300,1000,3000):_write(outdir/f'rel_elev_{radius}m.tif',relative_elevation(elev,mean),profile)
        del denom,sums,mean,mn
    pct=_local_percentile(elev,valid,size=2*round(1000/res)+1,bins=128);_write(outdir/'elevation_percentile_1km.tif',pct,profile);del pct
    # Fill masked cells from their nearest valid neighbour only for gradient evaluation.
    nearest=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
    safe=elev.copy();safe[~valid]=elev[tuple(nearest[:,~valid])]
    gy,gx=np.gradient(safe,res,res);slope=np.hypot(gx,gy).astype(np.float32);slope[~valid]=np.nan
    _write(outdir/'slope.tif',slope,profile)
    filled=fill_depressions(elev,valid);filldepth=np.maximum(filled-elev,0).astype(np.float32);filldepth[~valid]=np.nan
    _write(outdir/'fill_depth.tif',filldepth,profile)
    flow=d8_flow_accumulation(filled,valid,res);flowlog=np.log1p(flow).astype(np.float32);flowlog[~valid]=np.nan
    _write(outdir/'flow_accumulation_log.tif',flowlog,profile)
    twi=np.log(np.maximum(flow*res,1e-6)/np.maximum(slope,1e-4)).astype(np.float32);twi[~valid]=np.nan
    _write(outdir/'twi.tif',twi,profile)
    water_any,water_major,coast=_water_masks(city,(height,width),transform,dstcrs)
    for key,seed in (('any',water_any),('major',water_major)):
        if seed.any():
            dist,indices=ndi.distance_transform_edt(~seed,sampling=(res,res),return_indices=True)
            hand=elev-elev[indices[0],indices[1]];dist=dist.astype(np.float32);dist[~valid]=np.nan;hand[~valid]=np.nan
            _write(outdir/f'dist_water_{key}_m.tif',dist,profile);_write(outdir/f'hand_{key}_m.tif',hand,profile)
            del dist,indices,hand
        else:
            print(f'{city}/{dem}: no {key} water pixels; distance/HAND rasters omitted')
    if coast.any():
        dist=ndi.distance_transform_edt(~coast,sampling=(res,res)).astype(np.float32);dist[~valid]=np.nan;_write(outdir/'dist_coast_m.tif',dist,profile)
    else:print(f'{city}/{dem}: coastline layer unavailable; coast distance skipped')
    return outdir,(height,width),epsg

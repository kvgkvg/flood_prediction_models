"""Daily rain/tide drivers from cached sources, with local-day semantics."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

LOCAL_TZ='Asia/Ho_Chi_Minh'
RAIN_FIELDS=['rain_total_mm','rain_max_1h_mm','rain_max_3h_mm','rain_max_6h_mm','rain_prev_24h_mm','rain_prev_72h_mm','rain_prev_7d_mm','rain_hours']

def _local_index(values):
    x=pd.DatetimeIndex(pd.to_datetime(values,errors='coerce'))
    if x.tz is None:return x
    return x.tz_convert(LOCAL_TZ).tz_localize(None)

def _cell_daily(hourly,lat,lon):
    d=hourly.copy();d['time']=_local_index(d.time);d=d.dropna(subset=['time']).sort_values('time').drop_duplicates('time').set_index('time')
    d=d.loc[(d.index>='2002-01-01')&(d.index<'2025-01-01')]
    if d.empty:return pd.DataFrame()
    # Preserve actual missing hours as missing; do not silently impute them to zero.
    rain=pd.to_numeric(d.precipitation,errors='coerce').astype(float)
    roll3=rain.rolling(3,min_periods=3).sum();roll6=rain.rolling(6,min_periods=6).sum()
    # Rolling windows are confined to each local calendar day, as at run time.
    roll3.loc[d.index.hour<2]=np.nan;roll6.loc[d.index.hour<5]=np.nan
    out=pd.DataFrame({'rain_total_mm':rain.resample('D').sum(min_count=1),'rain_max_1h_mm':rain.resample('D').max(),'rain_max_3h_mm':roll3.resample('D').max(),'rain_max_6h_mm':roll6.resample('D').max(),'rain_hours':(rain>0).resample('D').sum(min_count=1)})
    daily=out.rain_total_mm
    out['rain_prev_24h_mm']=daily.shift(1).rolling(1,min_periods=1).sum()
    out['rain_prev_72h_mm']=daily.shift(1).rolling(3,min_periods=3).sum()
    out['rain_prev_7d_mm']=daily.shift(1).rolling(7,min_periods=7).sum()
    out=out.reset_index(names='date');out['cell_lat']=float(lat);out['cell_lon']=float(lon)
    return out[['date','cell_lat','cell_lon']+RAIN_FIELDS]

def load_hourly_rain(city,root=Path('.'),end='2024-12-31'):
    frames=[]
    for p in sorted((root/'data/raw/open_meteo'/city).glob('*.parquet')):
        try:year=int(p.stem.rsplit('_',1)[1])
        except (ValueError,IndexError):continue
        if year>2024:continue
        x=pd.read_parquet(p,columns=['time','precipitation','latitude_returned','longitude_returned'])
        x['time']=_local_index(x.time);x=x.loc[(x.time<'2025-01-01')&(x.time<=pd.Timestamp(end)+pd.Timedelta(hours=23))]
        frames.append(x)
    if not frames:return pd.DataFrame(columns=['time','precipitation','cell_lat','cell_lon'])
    d=pd.concat(frames,ignore_index=True).rename(columns={'latitude_returned':'cell_lat','longitude_returned':'cell_lon'})
    return d.drop_duplicates(['time','cell_lat','cell_lon']).sort_values(['cell_lat','cell_lon','time']).reset_index(drop=True)

def build_rain_drivers(city,root=Path('.')):
    hourly=load_hourly_rain(city,root)
    if hourly.empty:raise FileNotFoundError(f'no cached ERA5 rain for {city}')
    cells=[]
    for (lat,lon),g in hourly.groupby(['cell_lat','cell_lon'],sort=True):cells.append(_cell_daily(g[['time','precipitation']],lat,lon))
    cell=pd.concat(cells,ignore_index=True).sort_values(['date','cell_lat','cell_lon'])
    # Cell-day completeness flags expose gaps rather than turning missing rain into dry weather.
    cityday=cell.groupby('date')[RAIN_FIELDS].agg(['max','mean']);cityday.columns=[f'{a}_{b}_cells' for a,b in cityday.columns];cityday=cityday.reset_index()
    n=cell.groupby('date').rain_total_mm.count().rename('rain_cells_available').reset_index();cityday=cityday.merge(n,on='date')
    out=root/'data/processed'/city;out.mkdir(parents=True,exist_ok=True)
    cell.to_parquet(out/'drivers_rain_cell_daily.parquet',index=False);cityday.to_parquet(out/'drivers_rain_daily.parquet',index=False)
    return cell,cityday

def build_tide_drivers(root=Path('.'),start='2002-01-01',end='2027-12-31'):
    from utide import solve,reconstruct
    p=root/'data/raw/uhslc_vung_tau/uhslc_vung_tau_hourly.csv'
    d=pd.read_csv(p,skiprows=[1]);d['time']=pd.to_datetime(d.time,utc=True,errors='coerce');d['sea_level']=pd.to_numeric(d.sea_level,errors='coerce')/1000.
    d=d.dropna(subset=['time','sea_level']);d=d[d.time<pd.Timestamp('2025-01-01',tz='UTC')].sort_values('time').drop_duplicates('time')
    # Bound UTide memory and preserve an independent DEV interval: only the five
    # calendar years immediately before 2023 identify the harmonic constants.
    fit=d[(d.time>=pd.Timestamp('2018-01-01',tz='UTC'))&(d.time<pd.Timestamp('2023-01-01',tz='UTC'))]
    if len(fit)>5*366*24+24:raise ValueError('UTide fit window exceeded five years')
    coef=solve(fit.time.dt.tz_localize(None).to_numpy(dtype='datetime64[ms]'),fit.sea_level.to_numpy(np.float64),lat=10.35,constit='auto',method='ols',trend=False,phase='Greenwich',nodal=True,conf_int='none',verbose=False)
    if len(coef.name)==0:raise ValueError('UTide selected no constituents; check timestamp/sea-level parsing')
    chunks=[];daily_chunks=[]
    for year in range(int(start[:4]),int(end[:4])+1):
        lo=max(pd.Timestamp(start),pd.Timestamp(f'{year}-01-01'));hi=min(pd.Timestamp(end),pd.Timestamp(f'{year}-12-31'))
        local_idx=pd.date_range(lo,hi+pd.Timedelta(hours=23),freq='h')
        utc_idx=local_idx.tz_localize(LOCAL_TZ).tz_convert('UTC')
        tide_times=utc_idx.tz_localize(None).to_numpy(dtype='datetime64[ms]')
        astr=reconstruct(tide_times,coef,min_SNR=0,min_PE=0,verbose=False).h
        hourly_y=pd.DataFrame({'time_utc':utc_idx,'astro_m':np.asarray(astr,dtype=np.float32)})
        hourly_y['date']=hourly_y.time_utc.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None).dt.normalize()
        chunks.append(hourly_y)
        daily_chunks.append(hourly_y.groupby('date').astro_m.agg(['max','min']).rename(columns={'max':'astro_daily_max_m','min':'astro_daily_min_m'}))
    hourly=pd.concat(chunks,ignore_index=True)
    observed=d.copy();observed['date']=observed.time.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None).dt.normalize()
    obs=observed.groupby('date').sea_level.max().rename('observed_daily_max_m')
    daily=pd.concat(daily_chunks).groupby(level=0).first().sort_index()
    daily['astro_max_3d_m']=daily.astro_daily_max_m.rolling(3,min_periods=3).max()
    daily=daily.join(obs).reset_index();daily['astro_vs_observed_residual_m']=daily.astro_daily_max_m-daily.observed_daily_max_m
    out=root/'data/processed/ho_chi_minh';out.mkdir(parents=True,exist_ok=True)
    hourly.to_parquet(out/'drivers_tide_hourly.parquet',index=False);daily.to_parquet(out/'drivers_tide_daily.parquet',index=False)
    return hourly,daily,coef

def build_route_cell_lookup(city,root=Path('.')):
    import pyarrow as pa,pyarrow.parquet as pq
    import shapely
    base=root/'data/processed'/city;cells=pd.read_parquet(base/'drivers_rain_cell_daily.parquet',columns=['cell_lat','cell_lon']).drop_duplicates().to_numpy(np.float32)
    source=base/'routes.parquet';dest=base/'route_driver_cells.parquet';writer=None;parts=[]
    pf=pq.ParquetFile(source)
    for batch in pf.iter_batches(batch_size=1500,columns=['route_id','geometry']):
        ids=batch.column('route_id');geoms=shapely.from_wkb(batch.column('geometry').to_pylist());mid=shapely.line_interpolate_point(geoms,.5,normalized=True)
        lat=np.asarray(shapely.get_y(mid),np.float32);lon=np.asarray(shapely.get_x(mid),np.float32)
        dlat=lat[:,None]-cells[None,:,0];dlon=(lon[:,None]-cells[None,:,1])*np.cos(np.deg2rad(lat[:,None]));nearest=np.argmin(dlat*dlat+dlon*dlon,axis=1)
        tab=pa.table({'route_id':ids,'cell_lat':cells[nearest,0],'cell_lon':cells[nearest,1]})
        if writer is None:writer=pq.ParquetWriter(dest,tab.schema,compression='zstd')
        writer.write_table(tab);parts.append(tab.num_rows)
    if writer:writer.close()
    return {'rows':sum(parts),'batches':len(parts)}

def build_all(root=Path('.')):
    result={}
    for city in ('ho_chi_minh','da_nang'):
        cells,days=build_rain_drivers(city,root);base=root/'data/processed'/city;lookup_path=base/'route_driver_cells.parquet'
        import pyarrow.parquet as pq
        n_routes=pq.ParquetFile(base/'routes.parquet').metadata.num_rows
        if lookup_path.exists() and pq.ParquetFile(lookup_path).metadata.num_rows==n_routes:
            lookup=pd.read_parquet(lookup_path,columns=['route_id','cell_lat','cell_lon'])
            valid=set(map(tuple,pd.read_parquet(base/'drivers_rain_cell_daily.parquet',columns=['cell_lat','cell_lon']).drop_duplicates().to_numpy(float)))
            if lookup.route_id.is_unique and set(map(tuple,lookup[['cell_lat','cell_lon']].drop_duplicates().to_numpy(float)))<=valid:lookup_rows=len(lookup)
            else:lookup_rows=build_route_cell_lookup(city,root)['rows']
        else:lookup_rows=build_route_cell_lookup(city,root)['rows']
        result[city]={'rain_cell_rows':len(cells),'rain_days':len(days),'rain_cells':int(cells[['cell_lat','cell_lon']].drop_duplicates().shape[0]),'routes':lookup_rows,'route_lookup_reused':lookup_path.exists()}
    hourly,daily,_=build_tide_drivers(root);result['tide']={'hourly':len(hourly),'days':len(daily),'observed_days':int(daily.observed_daily_max_m.notna().sum())}
    return result

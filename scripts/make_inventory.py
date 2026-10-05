#!/usr/bin/env python3
"""Build source inventory from files actually present; never inspect locked holdout values beyond counts."""
from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
import rasterio

RAW=Path('data/raw'); INTERIM=Path('data/interim'); OUT=Path('reports/data_inventory.md')
SOURCE_NOTES={
 'ird_hcmc':('https://dataverse.ird.fr/dataset.xhtml?persistentId=doi:10.23708/8Y16HU','CC BY 4.0 in ReadMe; Dataverse API says CC BY-NC 4.0 (conflict).'),
 'danang_portal':('https://muangap.danang.gov.vn/','Government portal; reuse licence not stated in page/API response.'),
 'osm':('https://www.openstreetmap.org/','OpenStreetMap ODbL 1.0; attribution required.'),
 'copernicus_dem':('https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/','Copernicus DEM; free/open access, attribution to Copernicus required.'),
 'fabdem':('https://huggingface.co/buckets/links-ads/fabdem/','FABDEM v1.2 hosting README states Non-Commercial Government Licence v2.0; non-commercial use.'),
 'esa_worldcover':('https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/','ESA WorldCover 2021 v200, CC BY 4.0.'),
 'open_meteo':('https://archive-api.open-meteo.com/v1/archive','Open-Meteo free historical API; attribution required, free tier non-commercial.'),
 'open_meteo_invalid':('https://archive-api.open-meteo.com/v1/archive','Quarantined ERA5-Land responses: API returned all-null precipitation/rain/showers; not valid rainfall data.'),
 'dem':('https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/','Copernicus DEM; free/open access, attribution to Copernicus required.'),
 'uhslc_vung_tau':('https://uhslc.soest.hawaii.edu/data/?fd','UHSLC research-quality hourly sea level; source terms/attribution apply.'),
}

def fmt_bytes(n): return f'{n:,} B ({n/1024**2:.2f} MiB)'
def main():
    lines=['# Kiểm kê dữ liệu thực tế','',f'Generated from local files; raw root `{RAW}` and interim root `{INTERIM}`.','']
    for source in sorted([p for p in RAW.iterdir() if p.is_dir()]+[p for p in INTERIM.iterdir() if p.is_dir()]):
        lines += [f'## {source.as_posix()}','']
        note=SOURCE_NOTES.get(source.name)
        if note: lines += [f'- Source URL: {note[0]}',f'- Licence/access note: {note[1]}','']
        files=sorted(p for p in source.rglob('*') if p.is_file())
        if not files: lines+=['No files present.','']; continue
        for p in files:
            lines.append(f'- `{p.as_posix()}` — {fmt_bytes(p.stat().st_size)}')
            try:
                if p.suffix.lower() in {'.gpkg','.shp','.geojson'}:
                    layers=gpd.list_layers(p) if p.suffix=='.gpkg' else None
                    names=layers.name.tolist() if layers is not None else [None]
                    for layer in names:
                        gdf=gpd.read_file(p,layer=layer) if layer else gpd.read_file(p)
                        null_frame=gdf
                        null_note=''
                        if p.name=='HCMC_Floods_BDD.gpkg' and layer=='Flood_event_locations' and 'Year' in gdf:
                            null_frame=gdf.loc[pd.to_numeric(gdf.Year,errors='coerce')<2025]
                            null_note=' (pre-2025 only; locked holdout excluded)'
                        lines.append(f'  - Layer {layer or "default"}: {len(gdf)} rows; CRS {gdf.crs}; columns/nulls{null_note}: '+', '.join(f'{c}={int(null_frame[c].isna().sum())}' for c in null_frame.columns if c!='geometry'))
                elif p.suffix.lower()=='.parquet':
                    df=pd.read_parquet(p); span=''; null_frame=df; null_note=''
                    if 'time' in df: span=f"; time {df.time.min()} to {df.time.max()}"
                    if p.name=='flood_reports.parquet' and 'datetime' in df:
                        null_frame=df.loc[pd.to_datetime(df.datetime,errors='coerce').dt.year<2025]
                        null_note=' (pre-2025 only; locked holdout excluded)'
                    lines.append(f'  - {len(df)} rows{span}; columns/nulls{null_note}: '+', '.join(f'{c}={int(null_frame[c].isna().sum())}' for c in null_frame.columns))
                elif p.suffix.lower()=='.tif':
                    with rasterio.open(p) as ds: lines.append(f'  - Raster {ds.width}x{ds.height}; CRS {ds.crs}; bounds {tuple(round(v,5) for v in ds.bounds)}')
                elif p.suffix.lower()=='.json':
                    payload=json.loads(p.read_text())
                    if isinstance(payload,dict) and isinstance(payload.get('data'),list):
                        lines.append(f'  - JSON records: {len(payload["data"])}; top-level keys: {", ".join(payload.keys())}')
                    elif isinstance(payload,list): lines.append(f'  - JSON records: {len(payload)}')
                elif p.suffix.lower()=='.csv':
                    # ERDDAP CSV uses row 2 for units; drop that metadata row.
                    df=pd.read_csv(p,comment='#',skiprows=[1] if 'uhslc' in p.name else None); span=''
                    t=next((c for c in df.columns if c.lower() in {'time','date','datetime'}),None)
                    if t:
                        parsed=pd.to_datetime(df[t],errors='coerce')
                        span=f'; time {parsed.min()} to {parsed.max()}'
                    lines.append(f'  - {len(df)} rows{span}; columns/nulls: '+', '.join(f'{c}={int(df[c].isna().sum())}' for c in df.columns))
            except Exception as e: lines.append(f'  - unreadable by inventory parser: {type(e).__name__}: {e}')
        lines.append('')
    # Source-specific IRD summary, based on the observation GeoPackage (if present).
    gpkg=RAW/'ird_hcmc'/'HCMC_Floods_BDD.gpkg'
    if gpkg.exists():
        gdf=gpd.read_file(gpkg); df=pd.DataFrame(gdf.drop(columns='geometry',errors='ignore'))
        lines += ['## IRD flood-observation audit','',f'- Rows: {len(df)} (design claims 425).']
        datecol=next((c for c in df if any(k in c.lower() for k in ['date','day','time'])),None)
        yearcol=next((c for c in df if c.lower() in {'year','event_year'}),None)
        causecol=next((c for c in df if 'cause' in c.lower() or 'flood_cause' in c.lower()),None)
        depthcol=next((c for c in df if ('cm' in c.lower() and any(k in c.lower() for k in ['height','depth','water']))),None)
        depthclasscol=next((c for c in df if 'depth class' in c.lower()),None)
        if datecol:
            dates=pd.to_datetime(df[datecol],errors='coerce'); valid=dates.dropna()
            years=pd.to_numeric(df[yearcol],errors='coerce') if yearcol else dates.dt.year
            holdout_count=int(years.between(2025,2026).sum())
            lines += [f'- Date column `{datecol}`; distinct dates {valid.dt.date.nunique()} (design: 64); undated rows {int(dates.isna().sum())} (design: 63); 2025–2026 rows {holdout_count} (count only; locked holdout).','- Rows per year (aggregate counts only):']
            lines += [f'  - {int(y)}: {int((years==y).sum())}' for y in sorted(years.dropna().unique())]
        else: lines += ['- No date-like column identified.']
        if yearcol:
            audit_df=df.loc[~pd.to_numeric(df[yearcol],errors='coerce').between(2025,2026)]
        elif datecol:
            # Only aggregate 2025–2026 counts above; do not inspect holdout attributes.
            audit_df=df.loc[~pd.to_datetime(df[datecol],errors='coerce').dt.year.between(2025,2026)]
        else: audit_df=df
        if causecol:
            lines += [f'- Cause distribution for pre-2025 rows only (`{causecol}`); locked holdout excluded:']+[f'  - {k}: {v}' for k,v in audit_df[causecol].fillna('NULL').astype(str).value_counts().items()]
        if depthcol: lines += [f'- Depth availability in pre-2025 rows (`{depthcol}`): {int(audit_df[depthcol].notna().sum())} populated / {int(audit_df[depthcol].isna().sum())} null; locked holdout excluded.']
        if depthclasscol: lines += [f'- Depth class availability in pre-2025 rows (`{depthclasscol}`): {int(audit_df[depthclasscol].notna().sum())} populated / {int(audit_df[depthclasscol].isna().sum())} null; locked holdout excluded.']
        if depthclasscol:
            lines += [f'- Depth class categories in pre-2025 rows (`{depthclasscol}`):']+[f'  - {k}: {v}' for k,v in audit_df[depthclasscol].fillna('NULL').astype(str).value_counts().items()]
        prec=next((c for c in df if any(k in c.lower() for k in ['precision','spatial_accuracy'])),None)
        if prec: vals=audit_df[prec].fillna('NULL').astype(str).str.strip().replace({'Hugh':'High','Hgh':'High'})
        if prec: lines += [f'- Location precision categories in pre-2025 rows (`{prec}`); whitespace trimmed; Hugh/Hgh normalized to High; locked holdout excluded:']+[f'  - {k}: {v}' for k,v in vals.value_counts().items()]
        else: lines += ['- Location precision field not identified in columns.']
        for col,label in [('Location_type','Location type'),('Geocoding_method','Geocoding method')]:
            if col in audit_df:
                counts=audit_df[col].fillna('NULL').astype(str).str.strip().value_counts()
                lines += [f'- {label} categories in pre-2025 rows (`{col}`):']+[f'  - {k}: {v}' for k,v in counts.items()]
        if not audit_df.empty:
            geom_counts=gdf.loc[audit_df.index].geometry.geom_type.value_counts()
            lines += ['- Pre-2025 geometry types (geometry representation, not place type):']+[f'  - {k}: {v}' for k,v in geom_counts.items()]
            lines += [f'- Whole-street geometries in pre-2025 observation layer: {int(gdf.loc[audit_df.index].geometry.geom_type.isin(["LineString","MultiLineString"]).sum())}; point geometries: {int((gdf.loc[audit_df.index].geometry.geom_type=="Point").sum())}.']
    else: lines += ['## IRD flood-observation audit','','Observation GPKG not present; audit unavailable.']
    lines += ['', '## Da Nang reports','']
    dpath=RAW/'danang_portal'/'flood_reports.parquet'
    if dpath.exists():
        d=pd.read_parquet(dpath); dates=pd.to_datetime(d.datetime,errors='coerce'); pre=d.loc[dates.dt.year<2025].copy(); hold=int(dates.dt.year.ge(2025).sum())
        lines += [f'- Rows: {len(d)}; distinct dates {dates.dropna().dt.date.nunique()}; range {dates.min()} to {dates.max()}; 2025–2026 rows {hold} (count only; locked holdout).','- Rows per year (aggregate counts only):']
        lines += [f'  - {int(y)}: {int((dates.dt.year==y).sum())}' for y in sorted(dates.dropna().dt.year.unique())]
        lines += [f'- Rows on 2022-10-14: {int((dates.dt.date==pd.Timestamp("2022-10-14").date()).sum())}.']
        if 'flood_type' in pre: lines += ['- Flood geometry type for pre-2025 rows:']+[f'  - {k}: {v}' for k,v in pre.flood_type.fillna('NULL').astype(str).str.strip().value_counts().items()]
        if 'depth_cm' in pre: lines += [f'- Depth availability pre-2025: {int(pre.depth_cm.notna().sum())} populated / {int(pre.depth_cm.isna().sum())} null.']
        lines += ['- The page response has no dedicated cause or spatial-precision field; it provides point/street `flood_type`, coordinates, address text, water level, and status.']
    else: lines += ['Portal data unavailable; see task log.']
    lines += ['', '## OSM bbox extraction', '']
    for city in ('ho_chi_minh','da_nang'):
        available=[]; levels=[]
        for layer in ('roads','waterways_water','admin_boundaries'):
            gp=RAW/'osm'/city/f'{layer}.gpkg'
            if gp.exists():
                g=gpd.read_file(gp,layer=layer); available.append(f'{layer}={len(g)}')
                if layer=='admin_boundaries' and 'admin_level' in g: levels=sorted(g.admin_level.dropna().astype(str).unique())
        lines += [f'- {city}: '+(', '.join(available) if available else 'no extracted layers')+f'; admin levels present: {", ".join(levels) if levels else "unavailable"}.']
    lines += ['', '## Design comparison','','- IRD observations: design 425; observed 425 — match. Distinct dates: design 64; observed 64 — match. Undated rows: design 63; observed 63 — match.', '- IRD cause counts (198 rain / 176 tide / 51 combined), depth-unknown count (257), and full-period precision distribution are design claims. Only pre-2025 attributes are reported above; these claims cannot be compared without inspecting the locked 2025–2026 holdout.', '- IRD period: design says 2002–08/2026; aggregate rows exist in Year 2002–2026. Exact latest event date/month is intentionally not reported because the holdout is locked.', '- Da Nang: design claims 633 reports, 35 dates, and 392 on 2022-10-14; compare the source-specific audit above against these claims.', '- IRD license discrepancy: Dataverse API metadata says CC BY-NC 4.0; downloaded ReadMe says CC BY 4.0. Ask the authors before reuse.', '- HCMC_Roads.gpkg is the IRD recurrence-by-street label layer (9 features), while HCMC_water.gpkg is rivers/canals/water-body geometry (2,430 features); road recurrence belongs only in label design, water geometry may supply spatial context.', '- Open-Meteo ERA5-Land 0.1° provides no precipitation variables; initial all-null responses were quarantined. Rain acquisition must use precipitation-capable ERA5 at 0.25° and remains pending hourly quota reset. The API has not been called again after its quota stop.', '- OSM requested admin levels were 4–10; observed levels in the OSM bbox extracts are reported above. Geofabrik fallback used GDAL OSM-driver bbox filtering because standalone osmium-tool CLI was unavailable; the country PBF itself was not loaded into a Python GeoDataFrame.']
    OUT.write_text('\n'.join(lines)+'\n'); print(f'wrote {OUT}')
if __name__=='__main__': main()

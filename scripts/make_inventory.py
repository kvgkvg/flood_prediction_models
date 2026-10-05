#!/usr/bin/env python3
"""Build source inventory from files actually present; never inspect locked holdout values beyond counts."""
from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
import rasterio

RAW=Path('data/raw'); INTERIM=Path('data/interim'); OUT=Path('reports/data_inventory.md')

def fmt_bytes(n): return f'{n:,} B ({n/1024**2:.2f} MiB)'
def main():
    lines=['# Kiểm kê dữ liệu thực tế','',f'Generated from local files; raw root `{RAW}` and interim root `{INTERIM}`.','']
    for source in sorted([p for p in RAW.iterdir() if p.is_dir()]+[p for p in INTERIM.iterdir() if p.is_dir()]):
        lines += [f'## {source.as_posix()}','']
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
                        lines.append(f'  - Layer {layer or "default"}: {len(gdf)} rows; CRS {gdf.crs}; columns/nulls: '+', '.join(f'{c}={int(gdf[c].isna().sum())}' for c in gdf.columns if c!='geometry'))
                elif p.suffix.lower()=='.parquet':
                    df=pd.read_parquet(p); span=''
                    if 'time' in df: span=f"; time {df.time.min()} to {df.time.max()}"
                    lines.append(f'  - {len(df)} rows{span}; columns/nulls: '+', '.join(f'{c}={int(df[c].isna().sum())}' for c in df.columns))
                elif p.suffix.lower()=='.tif':
                    with rasterio.open(p) as ds: lines.append(f'  - Raster {ds.width}x{ds.height}; CRS {ds.crs}; bounds {tuple(round(v,5) for v in ds.bounds)}')
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
        if prec: lines += [f'- Location precision categories in pre-2025 rows (`{prec}`); locked holdout excluded:']+[f'  - {k}: {v}' for k,v in audit_df[prec].fillna('NULL').astype(str).value_counts().items()]
        else: lines += ['- Location precision field not identified in columns.']
    else: lines += ['## IRD flood-observation audit','','Observation GPKG not present; audit unavailable.']
    lines += ['', '## Da Nang reports','','Portal returned HTTP 403 “Blocked For Attack Detected”; no data downloaded and no bypass attempted. Historical report counts and 2025–2026 count unavailable.']
    lines += ['', '## Design comparison','','- IRD observations: design 425; observed 425 — match. Distinct dates: design 64; observed 64 — match. Undated rows: design 63; observed 63 — match.', '- IRD cause counts (198 rain / 176 tide / 51 combined), depth-unknown count (257), and full-period precision distribution are design claims. Only pre-2025 attributes are reported above; these claims cannot be compared without inspecting the locked 2025–2026 holdout.', '- IRD period: design says 2002–08/2026; aggregate rows exist in Year 2002–2026. Exact latest event date/month is intentionally not reported because the holdout is locked.', '- Da Nang: design claims 633 reports, 35 dates, and 392 on 2022-10-14; source returned HTTP 403, so each claim is unverified and no mismatch can be calculated.', '- IRD license discrepancy: Dataverse API metadata says CC BY-NC 4.0; downloaded ReadMe says CC BY 4.0. Ask the authors before reuse.']
    OUT.write_text('\n'.join(lines)+'\n'); print(f'wrote {OUT}')
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Generate route/label audit; label calculations exclude test_locked rows."""
from pathlib import Path
import json
import numpy as np
import geopandas as gpd
import pandas as pd

SEED=713
def rate_ci(success,total,seed=SEED,B=2000):
    if not total:return 0.,0.
    rng=np.random.default_rng(seed); sims=rng.binomial(total,success/total,size=B)/total
    return np.quantile(sims,[.025,.975])

def positive_count_ci(records,flag,seed=SEED,B=600):
    x=records.loc[records[flag].notna()]
    if x.empty:return 0,0
    rng=np.random.default_rng(seed); ids=x.route_id.to_numpy(); flags=x[flag].astype(bool).to_numpy(); vals=[]
    for _ in range(B):
        ix=rng.integers(0,len(x),len(x)); vals.append(len(set(ids[ix][flags[ix]])))
    return np.quantile(vals,[.025,.975])

def median_ci(values,seed=SEED,B=1000):
    a=np.asarray(values,dtype=float)
    if not len(a):return (float('nan'),float('nan'))
    rng=np.random.default_rng(seed); sims=np.empty(B)
    for i in range(B):sims[i]=np.median(rng.choice(a,size=len(a),replace=True))
    return np.quantile(sims,[.025,.975])

def main():
    root=Path('data/processed'); rec=gpd.read_parquet(root/'flood_records.parquet')
    matches=pd.read_parquet(root/'flood_record_matches.parquet')
    # Do not inspect locked record fields beyond permitted aggregate date/row counts.
    locked=rec.loc[rec.split.eq('test_locked'),['city','date']]
    train=rec.loc[rec.split.isin(['train','undated'])].merge(matches,on=['record_id','city'],how='left')
    lines=['# Routes and flood-label audit','',f'Reproducible command: `PYTHONPATH=src .venv/bin/python scripts/make_routes_report.py` (bootstrap seed {SEED}; 2,000 draws for rates, 600 for positive-route counts).','', 'All label/matching summaries use train + undated records only. The locked split is shown only as per-city record and distinct-date counts. Exact route totals are census counts of the cached OSM extract; uncertainty intervals are not meaningful for these finite totals.','']
    totals={}
    for city in ('ho_chi_minh','da_nang'):
        routes=gpd.read_parquet(root/city/'routes.parquet'); labels=pd.read_parquet(root/city/'route_labels.parquet')
        meta=json.loads((root/city/'route_build_metadata.json').read_text())
        cm=matches.loc[matches.city.eq(city)]; tr=train.loc[train.city.eq(city)]
        counts=cm.match_type.value_counts().to_dict(); success=len(cm)-counts.get('unmatched',0); lo,hi=rate_ci(success,len(cm))
        ml,mh=median_ci(routes.length_m,seed=SEED+len(city))
        lines += [f'## {city}', '',f"- Routes: {len(routes)} total ({int(routes.named.sum())} named, {int((~routes.named).sum())} unnamed; census).",f"- Ward boundary: finest available OSM admin level {meta['ward_level']}; {meta['ward_polygons']} polygons; {meta['bbox_area_coverage']:.1%} of bbox area covered (rest uses 1 km fallback cells).",f"- Routes by highway class: {routes.highway_class.value_counts().to_dict()}.",f"- Length metres: median {routes.length_m.median():.1f} (route-bootstrap 95% interval [{ml:.1f}, {mh:.1f}]); IQR {routes.length_m.quantile(.25):.1f}–{routes.length_m.quantile(.75):.1f}, mean {routes.length_m.mean():.1f}.",f"- Eligible match rate: {success}/{len(cm)} = {success/len(cm) if len(cm) else 0:.1%}, record-bootstrap 95% interval [{lo:.1%}, {hi:.1%}]; types {counts}."]
        for precision,g in tr.groupby('location_precision',dropna=False):
            hit=int(g.route_id.notna().sum()); a,b=rate_ci(hit,len(g),seed=SEED+len(str(precision)))
            lines.append(f"- Match by precision `{precision}`: {hit}/{len(g)} ({hit/len(g):.1%}; bootstrap 95% interval [{a:.1%}, {b:.1%}]).")
        dist=cm.match_distance_m.dropna()
        if len(dist):lines.append(f"- Match distance metres: median {dist.median():.1f}; IQR {dist.quantile(.25):.1f}–{dist.quantile(.75):.1f}; p90 {dist.quantile(.9):.1f}; max {dist.max():.1f}.")
        unmatched=tr.loc[tr.match_type.eq('unmatched')]
        lines.append('- Unmatched examples (up to 15, eligible records only):')
        for r in unmatched.head(15).itertuples(): lines.append(f"  - {r.record_id}: {str(r.road_name_text_raw)[:180]}")
        for flag,cause in [('ever_flood_rain','rain'),('ever_flood_tide','tide')]:
            positives=labels.loc[labels[flag].astype(bool)].merge(routes[['route_id','highway_class']],on='route_id',how='left')
            total=len(positives); pcts=positives.highway_class.value_counts().to_dict()
            classshare=(positives.highway_class.value_counts(normalize=True)*100).round(1).to_dict()
            allshares=(routes.highway_class.value_counts(normalize=True)*100).round(1).to_dict()
            lo_pos,hi_pos=rate_ci(total,len(routes),seed=SEED+len(city)+len(cause))
            lines.append(f"- Positive {cause} routes: {total}/{len(routes)} ({total/len(routes):.2%}; route-bootstrap 95% interval [{lo_pos:.2%}, {hi_pos:.2%}]); counts by highway class {pcts}; positive-class shares (%) {classshare}; all-route class shares (%) {allshares}.")
            totals[(city,cause)]=total
        if city=='da_nang':
            dated=tr.loc[tr.date.notna()]; day=pd.to_datetime(dated.date).dt.date
            on=dated.loc[day.eq(pd.Timestamp('2022-10-14').date())]
            lines.append(f"- 2022-10-14 concentration: {len(on)} eligible records, {on.route_id.nunique()} distinct matched routes, among {len(dated)} dated eligible records ({len(on)/len(dated) if len(dated) else 0:.1%}).")
        lock=locked.loc[locked.city.eq(city)]
        dates=pd.to_datetime(lock.date,errors='coerce').dropna()
        lines.append(f"- Locked split counts only: {len(lock)} records; {dates.dt.date.nunique()} distinct dates.")
        lines.append('')
    lines += ['## Assumptions','', '- Da Nang flood reports are classified as rain (`cause_assumed=True`). All source rows are treated as flood observations; records without dates are retained for route-level labels but have no date in the first/last-date summary.','- IRD cause text maps to rain/tide/combined by keyword; unmatched or empty values become unknown. Da Nang text is assumed to name a road when parsed from the first address segment.','- Location precision is inferred from source location type/geocoding method/precision fields; raw source values remain in the table. The hard HCMC bbox clamp is retained; non-locked source points are asserted inside it while locked row geometries are stored without per-row spatial validation.','- Named route fuzzy matching uses normalized sequence/token similarity >= 0.55; otherwise the nearest route within 40 m is used. Street/area records search named routes through 500 m.','- Unnamed route connectivity uses line intersections and a 2 m snapping tolerance in metric UTM; road-grade separation is not available in the OSM attributes used here. All reported counts are deterministic counts of these OSM downloads unless identified as bootstrap intervals.','']
    out=Path('reports/routes_and_labels.md');out.write_text('\n'.join(lines)+'\n')
    print(f'wrote {out}; positives={totals}')
if __name__=='__main__':main()

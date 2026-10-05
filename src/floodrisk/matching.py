"""Training-eligible flood record to route matcher."""
from __future__ import annotations
from difflib import SequenceMatcher
import re
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from floodrisk.records import normalize_name

def _similar(a,b):
    a=normalize_name(a); b=normalize_name(b)
    if not a or not b:return 0.
    ta=set(a.split());tb=set(b.split())
    jac=len(ta&tb)/len(ta|tb) if ta|tb else 0
    return max(jac,SequenceMatcher(None,a,b).ratio())

def _parse_street(raw):
    s=str(raw or '').strip()
    if not s:return ''
    # Portal addresses generally put house number + road before the first comma.
    s=s.split(',')[0].strip()
    s=re.sub(r'^(?:số\s*)?\d+[a-zA-Z]?\s+','',s,flags=re.I)
    return s

def match_records(records,routes_by_city):
    # Locked records are filtered before any spatial or text matching.
    eligible=records.loc[records.split.isin(['train','undated'])].copy()
    outputs=[]
    for city,df in eligible.groupby('city',sort=True):
        routes=routes_by_city[city].copy()
        metric=32648 if city=='ho_chi_minh' else 32649
        rmet=routes.to_crs(metric); sidx=rmet.sindex
        for r in df.itertuples(index=False):
            point=gpd.GeoSeries([Point(float(r.lon),float(r.lat))],crs=4326).to_crs(metric).iloc[0]
            norm=normalize_name(_parse_street(r.road_name_text)); radius=500 if r.location_precision in ('street','area') and norm else 150
            hits=list(sidx.query(point.buffer(radius),predicate='intersects'))
            if not hits:
                outputs.append({'record_id':r.record_id,'city':city,'route_id':None,'match_type':'unmatched','match_distance_m':None});continue
            distances=[]
            for j in hits:
                route=rmet.iloc[j];dist=point.distance(route.geometry)
                if dist<=radius:distances.append((dist,j,route))
            name_matches=[x for x in distances if x[2].get('named',False) and _similar(norm,x[2].get('name_norm'))>=0.55]
            if name_matches:
                dist,j,route=min(name_matches,key=lambda x:(x[0],str(x[2].route_id))); typ='name+distance'
            else:
                near=[x for x in distances if x[0]<=40]
                if near:dist,j,route=min(near,key=lambda x:(x[0],str(x[2].route_id)));typ='distance'
                else:dist=None;route=None;typ='unmatched'
            outputs.append({'record_id':r.record_id,'city':city,'route_id':route.route_id if route is not None else None,'match_type':typ,'match_distance_m':float(dist) if dist is not None else None})
    return pd.DataFrame(outputs,columns=['record_id','city','route_id','match_type','match_distance_m'])

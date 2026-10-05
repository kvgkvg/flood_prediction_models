"""Build stable street/ward route units from cached OSM ways."""
from __future__ import annotations
import json, math, re
from collections import defaultdict, Counter
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString, box
from shapely.ops import unary_union
from floodrisk.cities import CITIES
from floodrisk.records import normalize_name, stable_route_id

VEHICLE={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service'}
ALLOW=VEHICLE|{x+'_link' for x in VEHICLE}

def _lines(g):
    if g is None or g.is_empty:return []
    if g.geom_type=='LineString':return [g] if g.length>0 else []
    if g.geom_type in ('MultiLineString','GeometryCollection'):
        return [x for z in g.geoms for x in _lines(z)]
    return []

def _tags(x):
    s=x or ''
    try:
        return {k.strip():v.strip() for k,v in re.findall(r'"([^"]+)"=>"([^"]*)"',s)}
    except Exception:return {}

def _mode(vals):
    vals=[str(v).strip() for v in vals if v is not None and str(v).strip() not in ('','nan','None')]
    return Counter(vals).most_common(1)[0][0] if vals else None

def _component_groups(items):
    """Connected components of unnamed way fragments, including T/cross junctions."""
    parent=list(range(len(items)))
    def find(a):
        while parent[a]!=a: parent[a]=parent[parent[a]];a=parent[a]
        return a
    def union(a,b):
        a=find(a);b=find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    endpoints=defaultdict(list)
    for i,x in enumerate(items):
        geom=x['geom']
        for p in (geom.coords[0],geom.coords[-1]): endpoints[(round(p[0]/2),round(p[1]/2))].append(i)
    for ix in endpoints.values():
        for j in ix[1:]:union(ix[0],j)
    if len(items)>1:
        geoms=gpd.GeoSeries([x['geom'] for x in items])
        sidx=geoms.sindex
        for i,x in enumerate(items):
            # Ways touching in their interior are connected too; 2 m tolerance
            # handles small OSM node-coordinate discrepancies.
            for j in sidx.query(x['geom'].buffer(2),predicate='intersects'):
                if j>i and x['geom'].distance(items[j]['geom'])<=2:union(i,int(j))
    groups=defaultdict(list)
    for i,x in enumerate(items):groups[find(i)].append(x)
    return list(groups.values())

def _emit_pieces(pieces,city,out,rel):
    named_groups=defaultdict(list); unnamed_by=defaultdict(list)
    for p in pieces:
        (named_groups[(p['ward'],p['name_norm'])] if p['named'] else unnamed_by[(p['ward'],p['highway'])]).append(p)
    groups=[]
    for (ward,norm),ps in named_groups.items():groups.append((ward,norm,True,ps))
    for (ward,_hwy),ps in unnamed_by.items():
        for comp in _component_groups(ps):groups.append((comp[0]['ward'],'',False,comp))
    for ward,norm,named,ps in groups:
        ids=sorted(set(p['way_id'] for p in ps)); rid=stable_route_id(city,ward,norm,named,ids)
        lengths=defaultdict(float)
        for p in ps:lengths[p['highway']]+=p['geom'].length
        hw=max(lengths,key=lengths.get)
        merged=unary_union([p['geom'] for p in ps]); lines=_lines(merged)
        if not lines:continue
        geom=MultiLineString(lines); total=sum(x.length for x in lines)
        denom=sum(p['geom'].length for p in ps)
        bridge=sum(p['geom'].length for p in ps if p['tags'].get('bridge','no') not in ('no','false','0'))/denom
        tunnel=sum(p['geom'].length for p in ps if p['tags'].get('tunnel','no') not in ('no','false','0'))/denom
        out.append({'route_id':rid,'name':_mode(p['name'] for p in ps) if named else None,'name_norm':norm or None,'ward_id':ward,'named':named,'highway_class':hw,'length_m':total,'n_ways':len(ids),'bridge_frac':bridge,'tunnel_frac':tunnel,'lanes':_mode(p['tags'].get('lanes') for p in ps),'maxspeed':_mode(p['tags'].get('maxspeed') for p in ps),'surface':_mode(p['tags'].get('surface') for p in ps),'geometry':geom})
        rel.extend({'way_id':wid,'route_id':rid} for wid in ids)

def build_routes(city,root=Path('.')):
    manifest=json.loads((root/'data/raw/osm/city_bboxes.json').read_text())
    if city in CITIES: bbox=CITIES[city].bbox
    elif city in manifest and (root/'data/raw/osm'/city/'roads.gpkg').exists(): bbox=tuple(manifest[city]['bbox'])
    else: raise ValueError(f'city {city} needs a CITIES entry or cached OSM layers and bbox manifest')
    lon0=(bbox[0]+bbox[2])/2; lat0=(bbox[1]+bbox[3])/2
    zone=int((lon0+180)//6)+1
    crs_metric=(32600 if lat0>=0 else 32700)+zone
    base=root/'data/raw/osm'/city; roads=gpd.read_file(base/'roads.gpkg'); admin=gpd.read_file(base/'admin_boundaries.gpkg')
    roads=roads.to_crs(crs_metric); admin=admin.to_crs(crs_metric)
    lev=admin.admin_level.astype(str); levels=sorted(lev.unique(),key=lambda x:int(x)); chosen=max(levels,key=int)
    wards=admin.loc[lev==chosen].copy().reset_index(drop=True)
    bb=gpd.GeoSeries([box(*bbox)],crs=4326).to_crs(crs_metric).iloc[0]
    area=bb.area; ward_union=unary_union(wards.geometry.values) if len(wards) else None
    cover=(ward_union.intersection(bb).area/area) if ward_union else 0
    roads=roads.loc[roads.highway.astype(str).isin(ALLOW)].copy()
    out=[]; rel=[]; piece_count=0; road_idx=roads.sindex
    def append_piece(ps):
        nonlocal piece_count
        piece_count+=len(ps); _emit_pieces(ps,city,out,rel)
    # Process one ward (or one 1 km fallback cell) at a time to cap transient
    # fragment memory while splitting cross-boundary OSM ways.
    for _,wardrow in wards.iterrows():
        poly=wardrow.geometry; wardid=str(wardrow.osm_id) if pd.notna(wardrow.get('osm_id')) else str(wardrow.get('name'))
        pieces=[]
        for ix in road_idx.query(poly,predicate='intersects'):
            r=roads.iloc[int(ix)]; geom=r.geometry
            tags=_tags(r['other_tags']); rawname=(tags.get('name') or ('' if pd.isna(r['name']) else str(r['name']))).strip(); norm=normalize_name(rawname)
            for line in _lines(geom.intersection(poly)):
                if line.length>0.1:pieces.append({'way_id':str(r['osm_id']),'name':rawname if norm else None,'name_norm':norm,'named':bool(norm),'ward':wardid,'highway':str(r['highway']),'geom':line,'tags':tags})
        append_piece(pieces)
    # Segments not covered by any ward polygon are clipped into 1 km UTM cells.
    fallback_region=bb.difference(ward_union) if ward_union is not None else bb
    if not fallback_region.is_empty:
        fg=[]; keep=[]
        for ix,geom in enumerate(roads.geometry):
            rem=geom.intersection(fallback_region)
            if not rem.is_empty and rem.length>0.1:fg.append(rem);keep.append(ix)
        fallback_roads=roads.iloc[keep].copy();fallback_roads.geometry=fg
        fallback_idx=fallback_roads.sindex
    else:
        fallback_roads=roads.iloc[0:0].copy();fallback_idx=fallback_roads.sindex
    minx,miny,maxx,maxy=bb.bounds
    for gx in range(math.floor(minx/1000),math.ceil(maxx/1000)):
        for gy in range(math.floor(miny/1000),math.ceil(maxy/1000)):
            cell=box(gx*1000,gy*1000,(gx+1)*1000,(gy+1)*1000); pieces=[]
            if fallback_region.intersection(cell).is_empty:continue
            for ix in fallback_idx.query(cell,predicate='intersects'):
                r=fallback_roads.iloc[int(ix)]; geom=r.geometry.intersection(cell)
                tags=_tags(r['other_tags']); rawname=(tags.get('name') or ('' if pd.isna(r['name']) else str(r['name']))).strip(); norm=normalize_name(rawname)
                for line in _lines(geom):
                    if line.length>0.1:pieces.append({'way_id':str(r['osm_id']),'name':rawname if norm else None,'name_norm':norm,'named':bool(norm),'ward':f'grid:{gx}:{gy}','highway':str(r['highway']),'geom':line,'tags':tags})
            append_piece(pieces)
    target=root/'data/processed'/city;target.mkdir(parents=True,exist_ok=True)
    rg=gpd.GeoDataFrame(out,geometry='geometry',crs=crs_metric).to_crs(4326)
    rg.to_parquet(target/'routes.parquet',index=False)
    pd.DataFrame(rel,columns=['way_id','route_id']).drop_duplicates().to_parquet(target/'route_ways.parquet',index=False)
    return rg,{'ward_level':int(chosen),'ward_polygons':len(wards),'bbox_area_coverage':float(cover),'roads_kept':len(roads),'road_pieces':piece_count}

#!/usr/bin/env python3
"""Fetch tiled OSM roads, waterways/water and admin boundaries using Overpass.
Requests are serialized and cached as GeoJSON response tiles before GeoPackage export.
"""
import json, time
from pathlib import Path
import requests
import geopandas as gpd
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import linemerge, unary_union, polygonize

BASE=Path('data/raw/osm'); ENDPOINTS=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']
STEP=0.20

def main():
    bboxes=json.loads((BASE/'city_bboxes.json').read_text())
    session=requests.Session(); endpoint_idx=0
    for slug,info in bboxes.items():
        west,south,east,north=info['bbox']; rows=[]
        for x in [west+i*STEP for i in range(int((east-west)/STEP)+1)]:
            for y in [south+i*STEP for i in range(int((north-south)/STEP)+1)]:
                w,s=x,y; e=min(x+STEP,east); n=min(y+STEP,north)
                if e<=w or n<=s: continue
                cache=BASE/slug/f'tile_{w:.3f}_{s:.3f}.json'; cache.parent.mkdir(parents=True,exist_ok=True)
                if cache.exists(): payload=json.loads(cache.read_text())
                else:
                    q=f'''[out:json][timeout:90];(way["highway"]({s},{w},{n},{e});way["waterway"~"river|canal|stream|drain"]({s},{w},{n},{e});way["natural"="water"]({s},{w},{n},{e});relation["boundary"="administrative"]["admin_level"~"^(4|5|6|7|8|9|10)$"]({s},{w},{n},{e}););out center tags geom;'''
                    response=None
                    errors=[]
                    for attempt in range(4):
                        ep=ENDPOINTS[endpoint_idx%len(ENDPOINTS)]
                        try:
                            response=session.post(ep,data={'data':q},timeout=150)
                            if response.status_code==200: break
                            errors.append(f'{ep}: HTTP {response.status_code} {response.text[:200]}')
                        except requests.RequestException as exc:
                            errors.append(f'{ep}: {type(exc).__name__}: {exc}')
                        endpoint_idx+=1; time.sleep(5*(attempt+1))
                    if response is None or response.status_code!=200: raise RuntimeError(f'Overpass tile failed {w},{s}: ' + ' | '.join(errors))
                    payload=response.json(); cache.write_text(json.dumps(payload)); time.sleep(1.1)
                for item in payload.get('elements',[]):
                    geom=None
                    if item.get('type')=='way' and item.get('geometry'):
                        coords=[(p['lon'],p['lat']) for p in item['geometry']]
                        if len(coords)>=2:
                            geom=Polygon(coords) if item.get('tags',{}).get('natural')=='water' else LineString(coords)
                    elif item.get('type')=='relation':
                        members=item.get('members',[])
                        outer=[]; inner=[]
                        for member in members:
                            coords=[(p['lon'],p['lat']) for p in member.get('geometry',[])]
                            if len(coords)>=2:
                                line=LineString(coords)
                                (inner if member.get('role')=='inner' else outer).append(line)
                        if outer:
                            shells=list(polygonize(linemerge(unary_union(outer))))
                            holes=list(polygonize(linemerge(unary_union(inner)))) if inner else []
                            polygons=[]
                            for shell in shells:
                                geom_part=shell.difference(unary_union([h for h in holes if shell.contains(h.representative_point())])) if holes else shell
                                if not geom_part.is_empty: polygons.extend(list(geom_part.geoms) if geom_part.geom_type=='MultiPolygon' else [geom_part])
                            if polygons: geom=polygons[0] if len(polygons)==1 else MultiPolygon(polygons)
                    if geom is not None:
                        tags=item.get('tags',{}); rows.append({'osm_type':item['type'],'osm_id':item['id'],'admin_level':tags.get('admin_level'),'highway':tags.get('highway'),'waterway':tags.get('waterway'),'natural':tags.get('natural'),'name':tags.get('name'),'tags':json.dumps(tags,ensure_ascii=False),'geometry':geom})
        if rows:
            gdf=gpd.GeoDataFrame(rows,geometry='geometry',crs='EPSG:4326').drop_duplicates(['osm_type','osm_id'])
            gdf.to_file(BASE/f'{slug}_features.gpkg',layer='features',driver='GPKG')
            print(slug,'features',len(gdf),'admin levels',sorted(gdf.admin_level.dropna().unique()))
        else: print(slug,'no features')
if __name__=='__main__': main()

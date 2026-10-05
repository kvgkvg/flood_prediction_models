#!/usr/bin/env python3
"""Fetch ESA WorldCover 2021 v200 map tiles intersecting city bboxes; crop rasters."""
from pathlib import Path
import json
import requests
import rasterio
from rasterio.windows import from_bounds

INDEX='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/esa_worldcover_2021_grid.geojson'
BASE='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map'
ROOT=Path('data/raw/esa_worldcover'); OUT=Path('data/interim/landcover')
def main():
    bboxes=json.loads(Path('data/raw/osm/city_bboxes.json').read_text()); ROOT.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    idx=ROOT/'grid.geojson'
    if not idx.exists():
        r=requests.get(INDEX,timeout=60); r.raise_for_status(); idx.write_bytes(r.content)
    features=json.loads(idx.read_text())['features']
    for slug,info in bboxes.items():
        w,s,e,n=info['bbox']; matches=[]
        from shapely.geometry import shape, box
        aoi=box(w,s,e,n)
        for f in features:
            if shape(f['geometry']).intersects(aoi): matches.append(f['properties'].get('ll_tile') or f['properties'].get('tile'))
        matches=sorted(set(filter(None,matches))); print(slug,'tiles',matches)
        paths=[]
        for tile in matches:
            path=ROOT/f'ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
            if not path.exists():
                url=f'{BASE}/{path.name}'; part=path.with_suffix('.tif.part')
                with requests.get(url,stream=True,timeout=180) as r:
                    r.raise_for_status()
                    with part.open('wb') as f:
                        for chunk in r.iter_content(1024*1024):
                            if chunk: f.write(chunk)
                part.replace(path)
            paths.append(path)
        for path in paths:
            with rasterio.open(path) as src:
                b=src.bounds; left=max(w,b.left); bottom=max(s,b.bottom); right=min(e,b.right); top=min(n,b.top)
                if left>=right or bottom>=top: continue
                win=from_bounds(left,bottom,right,top,src.transform).round_offsets().round_lengths()
                arr=src.read(window=win); trans=src.window_transform(win); profile=src.profile.copy(); profile.update(width=arr.shape[2],height=arr.shape[1],transform=trans,compress='deflate')
                dest=OUT/f'{slug}_{path.stem}.tif'
                with rasterio.open(dest,'w',**profile) as dst: dst.write(arr)
                print(dest,dest.stat().st_size)
if __name__=='__main__':main()

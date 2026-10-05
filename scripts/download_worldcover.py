#!/usr/bin/env python3
"""Fetch ESA WorldCover 2021 v200 map tiles intersecting city bboxes; crop rasters."""
from pathlib import Path
import json
import requests
import rasterio
from rasterio.windows import from_bounds

BASE='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map'
ROOT=Path('data/raw/esa_worldcover'); OUT=Path('data/interim/landcover')
def main():
    bboxes=json.loads(Path('data/raw/osm/city_bboxes.json').read_text()); ROOT.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    for slug,info in bboxes.items():
        w,s,e,n=info['bbox']
        import math
        lons=range(math.floor(w/3)*3, math.floor((e-1e-10)/3)*3+1, 3)
        lats=range(math.floor(s/3)*3, math.floor((n-1e-10)/3)*3+1, 3)
        def tag(v,axis): return ('N' if v>=0 else 'S')+f'{abs(v):02d}' if axis=='lat' else ('E' if v>=0 else 'W')+f'{abs(v):03d}'
        matches=sorted({tag(lat,'lat')+tag(lon,'lon') for lat in lats for lon in lons}); print(slug,'tiles',matches)
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
                b=src.bounds; pad=0.0002
                left=max(w-pad,b.left); bottom=max(s-pad,b.bottom); right=min(e+pad,b.right); top=min(n+pad,b.top)
                if left>=right or bottom>=top: continue
                win=from_bounds(left,bottom,right,top,src.transform).round_offsets().round_lengths()
                arr=src.read(window=win); trans=src.window_transform(win); profile=src.profile.copy(); profile.update(width=arr.shape[2],height=arr.shape[1],transform=trans,compress='deflate')
                dest=OUT/f'{slug}_{path.stem}.tif'
                with rasterio.open(dest,'w',**profile) as dst: dst.write(arr)
                print(dest,dest.stat().st_size)
if __name__=='__main__':main()

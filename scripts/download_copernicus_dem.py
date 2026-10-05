#!/usr/bin/env python3
"""Download required Copernicus GLO-30 COG tiles and crop mosaics by city bbox."""
from pathlib import Path
import json, math
import requests
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from shapely.geometry import box, mapping

ROOT=Path('data/raw/copernicus_dem'); OUT=Path('data/interim/dem')
BASE='https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com'

def tile_name(lat,lon):
    ns='N' if lat>=0 else 'S'; ew='E' if lon>=0 else 'W'
    return f'Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM'

def main():
    bboxes=json.loads(Path('data/raw/osm/city_bboxes.json').read_text())
    for slug,info in bboxes.items():
        w,s,e,n=info['bbox']; paths=[]
        for lat in range(math.floor(s),math.ceil(n)):
            for lon in range(math.floor(w),math.ceil(e)):
                name=tile_name(lat,lon); path=ROOT/(name+'.tif'); path.parent.mkdir(parents=True,exist_ok=True)
                if not path.exists():
                    url=f'{BASE}/{name}/{name}.tif'; part=path.with_suffix('.tif.part')
                    with requests.get(url,stream=True,timeout=180) as r:
                        r.raise_for_status()
                        with part.open('wb') as f:
                            for chunk in r.iter_content(1024*1024):
                                if chunk: f.write(chunk)
                    part.replace(path)
                paths.append(path)
        sources=[rasterio.open(p) for p in paths]
        try:
            pad=0.0001
            mosaic,trans=merge(sources,bounds=(w-pad,s-pad,e+pad,n+pad))
            profile=sources[0].profile.copy(); profile.update(height=mosaic.shape[1],width=mosaic.shape[2],transform=trans,compress='deflate',tiled=True)
            raw=OUT/f'{slug}_copernicus_glo30.tif'; raw.parent.mkdir(parents=True,exist_ok=True)
            with rasterio.open(raw,'w',**profile) as dst: dst.write(mosaic)
            print(slug,raw,raw.stat().st_size,'bbox',w,s,e,n)
        finally:
            for src in sources: src.close()
if __name__=='__main__':main()

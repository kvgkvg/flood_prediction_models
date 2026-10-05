#!/usr/bin/env python3
"""Build current city FABDEM crops from already-cached source tiles; no network."""
from pathlib import Path
import math
import rasterio
from rasterio.merge import merge
from floodrisk.cities import CITIES

ROOT=Path('data/raw/fabdem'); OUT=Path('data/interim/dem')
def main():
    for city,item in CITIES.items():
        w,s,e,n=item.bbox; srcs=[]
        for lat in range(math.floor(s),math.ceil(n)):
            for lon in range(math.floor(w),math.ceil(e)):
                path=ROOT/f"N{(lat//10)*10:02d}E{(lon//10)*10:03d}-N{(lat//10)*10+10:02d}E{(lon//10)*10+10:03d}_FABDEM_V1-2"/f'N{lat:02d}E{lon:03d}_FABDEM_V1-2.tif'
                if not path.exists():raise FileNotFoundError(path)
                srcs.append(rasterio.open(path))
        try:
            data,transform=merge(srcs,bounds=(w-.001,s-.001,e+.001,n+.001))
            profile=srcs[0].profile.copy();profile.update(width=data.shape[2],height=data.shape[1],transform=transform,compress='deflate',tiled=True)
            dest=OUT/f'{city}_fabdem_v1_2.tif';OUT.mkdir(parents=True,exist_ok=True)
            with rasterio.open(dest,'w',**profile) as dst:dst.write(data)
            print(city,dest,dest.stat().st_size)
        finally:
            for src in srcs:src.close()
if __name__=='__main__':main()

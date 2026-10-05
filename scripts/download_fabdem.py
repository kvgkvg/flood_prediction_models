#!/usr/bin/env python3
"""Inspect FABDEM V1-2 tile sizes for city bbox and download if needed total <12 GB.
Then mosaic/crop by city. Raw tiles are COGs and Downloads resume via HTTP Range.
"""
from pathlib import Path
import json, math, re
import requests, rasterio
from rasterio.merge import merge
BASE='https://huggingface.co/buckets/links-ads/fabdem/resolve/tiles'
ROOT=Path('data/raw/fabdem'); OUT=Path('data/interim/dem')
def ident(lat,lon):
    return f"{'N' if lat>=0 else 'S'}{abs(lat):02d}{'E' if lon>=0 else 'W'}{abs(lon):03d}"
def url_for(lat,lon):
    group=f"{'N' if lat>=0 else 'S'}{(abs(lat)//10)*10:02d}{'E' if lon>=0 else 'W'}{(abs(lon)//10)*10:03d}-{'N' if lat>=0 else 'S'}{(abs(lat)//10)*10+10:02d}{'E' if lon>=0 else 'W'}{(abs(lon)//10)*10+10:03d}_FABDEM_V1-2"
    tile=f'{ident(lat,lon)}_FABDEM_V1-2.tif'
    return group,tile,f'{BASE}/{group}/{tile}'
def main():
    bboxes=json.loads(Path('data/raw/osm/city_bboxes.json').read_text()); tiles={}
    for slug,info in bboxes.items():
        w,s,e,n=info['bbox']
        for lat in range(math.floor(s),math.ceil(n)):
            for lon in range(math.floor(w),math.ceil(e)):
                group,tile,url=url_for(lat,lon); tiles[(group,tile)]=url
    sess=requests.Session(); sizes={}
    for key,url in tiles.items():
        r=sess.head(url,allow_redirects=True,timeout=60); r.raise_for_status(); sizes[key]=int(r.headers.get('content-length',0))
    total=sum(sizes.values()); print('required tiles',len(tiles),'aggregate bytes',total)
    if not total or total>=12*1024**3: raise SystemExit('FABDEM needed tile size unknown or >=12 GiB; no download')
    # Measure an actual ranged transfer before writing more data. Include only
    # bytes still needed for incomplete tiles in the ETA.
    first_url=next(iter(tiles.values())); import time
    t0=time.monotonic()
    with sess.get(first_url,headers={'Range':'bytes=0-1048575'},stream=True,allow_redirects=True,timeout=60) as r:
        r.raise_for_status(); sampled=sum(len(c) for c in r.iter_content(256*1024) if c)
    speed=sampled/max(time.monotonic()-t0,0.01)
    remain=sum(max(0,size-((ROOT/key[0]/key[1]).stat().st_size if (ROOT/key[0]/key[1]).exists() else 0)) for key,size in sizes.items())
    eta=remain/max(speed,1)
    print(f'FABDEM sample={sampled} B speed={speed:.0f} B/s; remaining={remain} B; ETA={eta:.0f} s; sample URL={first_url}')
    if eta>=900: raise SystemExit(f'FABDEM below 15-minute speed threshold; size={total} B; URL={first_url}; resumable files retained')
    for (group,tile),url in tiles.items():
        dest=ROOT/group/tile; dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.stat().st_size==sizes[(group,tile)]: continue
        offset=dest.stat().st_size if dest.exists() else 0; headers={'Range':f'bytes={offset}-'} if offset else {}
        with sess.get(url,headers=headers,stream=True,timeout=180) as r:
            if offset and r.status_code!=206: offset=0
            r.raise_for_status(); mode='ab' if offset else 'wb'
            with dest.open(mode) as f:
                for chunk in r.iter_content(1024*1024):
                    if chunk:f.write(chunk)
        if dest.stat().st_size!=sizes[(group,tile)]:raise IOError(f'incomplete tile {dest}')
    for slug,info in bboxes.items():
        w,s,e,n=info['bbox']
        paths=[]
        for lat in range(math.floor(s),math.ceil(n)):
            for lon in range(math.floor(w),math.ceil(e)):
                group,tile,_=url_for(lat,lon); paths.append(ROOT/group/tile)
        srcs=[rasterio.open(p) for p in paths]
        try:
            pad=0.0001; data,transform=merge(srcs,bounds=(w-pad,s-pad,e+pad,n+pad)); profile=srcs[0].profile.copy();profile.update(width=data.shape[2],height=data.shape[1],transform=transform,compress='deflate')
            OUT.mkdir(parents=True,exist_ok=True)
            with rasterio.open(OUT/f'{slug}_fabdem_v1_2.tif','w',**profile) as dst:dst.write(data)
        finally:
            for src in srcs:src.close()
if __name__=='__main__':main()

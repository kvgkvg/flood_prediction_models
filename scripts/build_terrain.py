#!/usr/bin/env python3
import argparse
from floodrisk.terrain import build_terrain

def main():
    p=argparse.ArgumentParser();p.add_argument('--city',required=True);p.add_argument('--dem',required=True,choices=['fabdem','copernicus']);a=p.parse_args()
    out,shape,epsg=build_terrain(a.city,a.dem)
    print(f'{a.city}/{a.dem}: grid={shape[1]}x{shape[0]} EPSG:{epsg}, outputs={len(list(out.glob("*.tif")))}')
if __name__=='__main__':main()

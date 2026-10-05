#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from floodrisk.routes import build_routes

def main():
 p=argparse.ArgumentParser();p.add_argument('--city',required=True);a=p.parse_args()
 routes,info=build_routes(a.city)
 Path(f'data/processed/{a.city}/route_build_metadata.json').write_text(json.dumps(info,indent=2))
 print(f"{a.city}: routes={len(routes)} named={int(routes.named.sum())} unnamed={int((~routes.named).sum())}; {info}")
if __name__=='__main__':main()

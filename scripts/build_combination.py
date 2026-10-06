#!/usr/bin/env python3
"""Fit FIT-only Model 1 susceptibility and construct daily P/hybrid alert indices."""
import argparse,json
from floodrisk.combine import build_combination

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true',help='fit small deterministic feature subset without saving artifacts');a=p.parse_args()
    print(json.dumps(build_combination(pilot=a.pilot,save=not a.pilot),indent=2,default=str))

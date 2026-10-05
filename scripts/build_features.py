#!/usr/bin/env python3
import argparse
from floodrisk.features import build_features

def main():
    p=argparse.ArgumentParser();p.add_argument('--city',required=True);a=p.parse_args()
    f,m=build_features(a.city)
    print(f'{a.city}: routes={len(f)} features={len(f.columns)-1}; manifest=data/processed/{a.city}/feature_manifest.json')
if __name__=='__main__':main()

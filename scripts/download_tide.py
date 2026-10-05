#!/usr/bin/env python3
"""Cache UHSLC hourly Vung Tau (UHSLC ID 383) record from public ERDDAP."""
from pathlib import Path
import requests
OUT=Path('data/raw/uhslc_vung_tau/uhslc_vung_tau_hourly.csv')
URL='https://pae-paha.pacioos.hawaii.edu/erddap/tabledap/uhslc_global_hourly_fast.csv'
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if OUT.exists() and OUT.stat().st_size: print(f'cached {OUT}'); return
    r=requests.get(URL+'?time,sea_level,quality,station_name,uhslc_id&uhslc_id=383',timeout=120)
    r.raise_for_status(); OUT.write_bytes(r.content); print(OUT,r.status_code,len(r.content))
if __name__=='__main__': main()

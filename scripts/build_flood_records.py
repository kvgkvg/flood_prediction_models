#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
from floodrisk.records import build_records

def main():
    out=Path('data/processed/flood_records.parquet');out.parent.mkdir(parents=True,exist_ok=True)
    records=build_records();records.to_parquet(out,index=False)
    # Holdout output is limited strictly to aggregate row/date counts.
    locked=records.loc[records.split.eq('test_locked'),['date']]
    dates=pd.to_datetime(locked.date,errors='coerce').dropna()
    print(f'{out}: rows={len(records)} CRS=EPSG:4326 locked_records={len(locked)} locked_distinct_dates={dates.dt.date.nunique()}')
    print('pre-holdout and undated counts:',records.loc[~records.split.eq('test_locked'),'city'].value_counts().to_dict())
if __name__=='__main__':main()

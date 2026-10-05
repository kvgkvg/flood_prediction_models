#!/usr/bin/env python3
from pathlib import Path
import geopandas as gpd
import pandas as pd
from floodrisk.records import build_route_labels
from floodrisk.matching import match_records

def main():
 root=Path('data/processed'); rec=gpd.read_parquet(root/'flood_records.parquet')
 routes={c:gpd.read_parquet(root/c/'routes.parquet') for c in ('ho_chi_minh','da_nang')}
 matches=match_records(rec,routes);matches.to_parquet(root/'flood_record_matches.parquet',index=False)
 # Only eligible splits are joined to labels; locked rows are never matched or aggregated.
 eligible=rec.loc[rec.split.isin(['train','train_undated'])].merge(matches,on=['record_id','city'],how='left')
 for city in routes:
  labels=build_route_labels(eligible.loc[eligible.city.eq(city)])
  labels.to_parquet(root/city/'route_labels.parquet',index=False)
 print(f'matches={len(matches)} eligible_records={len(eligible)}; both locked splits excluded before matching and labels')
 print(matches.groupby(['city','match_type']).size().to_dict())
if __name__=='__main__':main()

"""Proximity to any OSM water feature baseline."""
def fit(train_df,feature_manifest,target):return None
def predict(model,df):return -df['fab_dist_any_water_min'].fillna(df['fab_dist_any_water_min'].median()).to_numpy(float)
M1_FEATURE_COUNT=1

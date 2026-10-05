"""Lowest FABDEM route elevation baseline."""
def fit(train_df,feature_manifest,target):return None
def predict(model,df):return -df['fab_elev_min'].fillna(df['fab_elev_min'].median()).to_numpy(float)
M1_FEATURE_COUNT=1

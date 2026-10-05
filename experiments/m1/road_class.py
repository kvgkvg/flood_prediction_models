"""Road class rank is a reporting-bias-only baseline."""
def fit(train_df,feature_manifest,target):return None
def predict(model,df):return df['road_highway_rank'].fillna(0).to_numpy(float)
M1_FEATURE_COUNT=1

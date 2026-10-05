"""Built-up fraction baseline for dense-settlement reporting bias."""
def fit(train_df,feature_manifest,target):return None
def predict(model,df):return df['lc_builtup_500m_frac'].fillna(df['lc_builtup_500m_frac'].median()).to_numpy(float)
M1_FEATURE_COUNT=1

"""Replacing exposure predictors by training medians at prediction time removes learned reporting bias."""
from experiments.m1._util import fit_lgbm,lightgbm_frame

EXPOSURE=('road_highway_rank','lanes','named','road_length_density_500m','road_intersections_300m','lc_builtup_200m_frac','lc_builtup_500m_frac','lc_tree_500m_frac','lc_grass_shrub_500m_frac','lc_cropland_500m_frac','lc_bare_500m_frac')
def fit(train_df,feature_manifest,target):
    b=fit_lgbm(train_df,feature_manifest,'all');x=lightgbm_frame(train_df,feature_manifest,'all')
    b['medians']={c:train_df[c].median() for c in EXPOSURE if c in train_df and c in x};b['modes']={c:train_df[c].mode(dropna=True).iloc[0] for c in EXPOSURE if c in train_df and c in x and not __import__('pandas').api.types.is_numeric_dtype(train_df[c])};return b
def predict(b,df):
    d=df.copy()
    for c,v in b['medians'].items():d[c]=v
    for c,v in b['modes'].items():d[c]=v
    from experiments.m1._util import predict_lgbm
    return predict_lgbm(b,d,{'feature_names':b['feature_names']})

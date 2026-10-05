"""A compact FABDEM physical feature set should reduce noise from duplicate raster predictors."""
from lightgbm import LGBMClassifier
from experiments.m1._util import lightgbm_frame

KEEP=('fab_elevation_min_cityrank','fab_elevation_mean_cityrank','fab_rel_elev_300m_min_cityrank','fab_rel_elev_1000m_min_cityrank','fab_fill_depth_mean_cityrank','fab_fill_depth_max_cityrank','fab_flow_accumulation_log_mean_cityrank','fab_twi_mean_cityrank','fab_dist_water_any_m_min_cityrank','fab_hand_any_m_min_cityrank','fab_dist_water_major_m_min_cityrank','fab_hand_major_m_min_cityrank','fab_slope_mean_cityrank','lc_tree_500m_frac_cityrank','lc_grass_shrub_500m_frac_cityrank','lc_cropland_500m_frac_cityrank','lc_bare_500m_frac_cityrank','road_highway_class','road_highway_rank_cityrank')
def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'cityrank');cols=[c for c in KEEP if c in x];x=x[cols]
    m=LGBMClassifier(n_estimators=120,max_depth=3,num_leaves=5,learning_rate=.04,reg_lambda=10,min_child_samples=15,random_state=516,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    m.fit(x,train_df.label.astype(int),sample_weight=train_df.sample_weight);return {'model':m,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(x)[:,1]

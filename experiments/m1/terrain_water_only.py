"""Removing all land-cover inputs tests whether hydrologic terrain alone transfers beyond urban exposure."""
from lightgbm import LGBMClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');cols=[c for c in x if c.startswith(('fab_','cop_')) and c.endswith('_cityrank')];x=x[cols]
    m=LGBMClassifier(n_estimators=140,max_depth=3,num_leaves=5,learning_rate=.035,reg_lambda=14,reg_alpha=2,min_child_samples=25,random_state=551,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    m.fit(x,train_df.label.astype(int),sample_weight=train_df.sample_weight);return {'model':m,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(x)[:,1]

"""A shallower regularized physical LightGBM should avoid fitting city-specific reporting structure."""
from lightgbm import LGBMClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');cols=list(x.columns);m=LGBMClassifier(n_estimators=100,max_depth=2,num_leaves=3,learning_rate=.025,reg_lambda=24,reg_alpha=4,min_child_samples=40,colsample_bytree=.75,random_state=220,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    m.fit(x,train_df.label.astype(int),sample_weight=train_df.sample_weight);return {'model':m,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(x)[:,1]

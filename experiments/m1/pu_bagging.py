"""Bagging positive-unlabeled LightGBM models can reduce noisy negative labels."""
import numpy as np
from lightgbm import LGBMClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');y=train_df.label.to_numpy(bool);p=np.flatnonzero(y);u=np.flatnonzero(~y)
    rng=np.random.default_rng(8841);models=[]
    for i in range(30):
        neg=rng.choice(u,min(len(u),5*len(p)),replace=False) if len(u) else u;ix=np.r_[p,neg]
        m=LGBMClassifier(n_estimators=20,max_depth=3,num_leaves=5,learning_rate=.05,reg_lambda=8,min_child_samples=12,random_state=8841+i,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
        m.fit(x.iloc[ix],y[ix],sample_weight=train_df.sample_weight.iloc[ix]);models.append(m)
    return {'models':models,'columns':list(x.columns),'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0)
    return np.mean([m.predict_proba(x)[:,1] for m in b['models']],axis=0)

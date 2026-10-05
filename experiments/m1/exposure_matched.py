"""Matching unlabeled negatives on exposure should reveal signal beyond reporting opportunity."""
import numpy as np,pandas as pd
from lightgbm import LGBMClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    d=train_df.reset_index(drop=True);y=d.label.to_numpy(bool);pos=np.flatnonzero(y);neg=np.flatnonzero(~y)
    road=d.get('road_highway_class',pd.Series('unknown',index=d.index)).astype(str)
    built=pd.to_numeric(d.get('lc_builtup_500m_frac',0),errors='coerce').fillna(-1);inter=pd.to_numeric(d.get('road_intersections_300m',0),errors='coerce').fillna(-1)
    b=pd.qcut(built.rank(method='first'),3,labels=False,duplicates='drop').astype(str);i=pd.qcut(inter.rank(method='first'),3,labels=False,duplicates='drop').astype(str)
    key=road+'|'+b+'|'+i; rng=np.random.default_rng(762);picked=[]
    for k,ids in pd.Series(pos).groupby(key.iloc[pos].to_numpy()):
        candidates=neg[key.iloc[neg].to_numpy()==k];
        if len(candidates):picked.extend(rng.choice(candidates,min(len(candidates),max(1,len(ids))),replace=False))
    ix=np.r_[pos,np.asarray(picked,dtype=int)] if picked else pos
    tr=d.iloc[ix].copy();x=lightgbm_frame(tr,feature_manifest,'phys_cityrank');yy=tr.label.to_numpy(bool)
    m=LGBMClassifier(n_estimators=120,max_depth=3,num_leaves=5,learning_rate=.04,reg_lambda=10,min_child_samples=15,random_state=762,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    m.fit(x,yy,sample_weight=tr.sample_weight);return {'model':m,'columns':list(x.columns),'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(x)[:,1]

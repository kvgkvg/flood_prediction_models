"""Monotone physical constraints should keep susceptibility directions coherent across cities."""
from lightgbm import LGBMClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'cityrank');cols=list(x.columns);constraints=[]
    for c in cols:
        base=c.replace('_cityrank','')
        if 'rel_elev' in base or 'hand_' in base or 'dist_water' in base:constraints.append(-1)
        elif any(z in base for z in ('fill_depth','flow_accumulation','twi')):constraints.append(1)
        else:constraints.append(0)
    m=LGBMClassifier(n_estimators=140,max_depth=3,num_leaves=5,learning_rate=.035,reg_lambda=12,min_child_samples=20,monotone_constraints=constraints,random_state=9401,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    m.fit(x,train_df.label.astype(int),sample_weight=train_df.sample_weight);return {'model':m,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(x)[:,1]

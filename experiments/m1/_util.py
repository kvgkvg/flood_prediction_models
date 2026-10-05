"""Shared narrowly scoped preprocessing for baseline scorers."""
import numpy as np
import pandas as pd

DESIGN_NUMERIC=['fab_elev_min','fab_elevation_mean','fab_rel_elev_300m_min','fab_rel_elev_300m_mean','fab_rel_elev_1000m_min','fab_rel_elev_1000m_mean','fab_dist_water_any_m_min','fab_hand_any_m_min','lc_builtup_200m_frac']

def design_frame(df):
    cols=[c for c in DESIGN_NUMERIC if c in df]
    x=df[cols].copy()
    if 'road_highway_class' in df:
        x['road_highway_class']=df.road_highway_class.astype('string').fillna('unknown')
        x=pd.get_dummies(x,columns=['road_highway_class'],dtype=float)
    return x

def lightgbm_frame(df,manifest,which):
    all_features=[c for c in manifest['feature_names'] if c in df.columns and c not in ('route_id','in_universe')]
    if which=='design':
        return design_frame(df)
    if which=='all':
        cols=[c for c in all_features if not c.endswith('_cityrank')]
    elif which=='cityrank':
        cols=[c for c in all_features if c.endswith('_cityrank') or c=='road_highway_class']
    elif which=='phys_cityrank':
        cols=[c for c in all_features if (c.startswith(('fab_','cop_','lc_')) and c.endswith('_cityrank') and not c.startswith(('lc_builtup','lc_intersection')))]
    else:raise ValueError(which)
    x=df[cols].copy()
    cats=[c for c in cols if c=='road_highway_class']
    for c in cats:x[c]=x[c].astype('string').fillna('unknown')
    if cats:x=pd.get_dummies(x,columns=cats,dtype=float)
    for c in x:
        if x[c].dtype=='bool':x[c]=x[c].astype('uint8')
    return x.replace([np.inf,-np.inf],np.nan)

def fit_lgbm(df,manifest,which):
    from lightgbm import LGBMClassifier
    x=lightgbm_frame(df,manifest,which);y=df.label.astype(int);w=df.sample_weight.astype(float)
    model=LGBMClassifier(n_estimators=160,max_depth=4,num_leaves=7,learning_rate=.035,reg_lambda=8.,reg_alpha=1.5,min_child_samples=30,subsample=.85,colsample_bytree=.8,subsample_freq=1,random_state=41073,n_jobs=6,verbosity=-1,deterministic=True,force_col_wise=True)
    model.fit(x,y,sample_weight=w)
    return {'model':model,'columns':list(x.columns),'which':which,'feature_names':list(manifest['feature_names'])}

def predict_lgbm(bundle,df,manifest):
    x=lightgbm_frame(df,manifest,bundle['which']).reindex(columns=bundle['columns'],fill_value=0)
    return bundle['model'].predict_proba(x)[:,1]

"""Reporting exposure alone explains route labels, without physical flood signals."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

EXPOSURE=['road_highway_rank','lanes','named','road_length_density_500m','road_intersections_300m','lc_builtup_200m_frac','lc_builtup_500m_frac','lc_tree_500m_frac','lc_grass_shrub_500m_frac','lc_cropland_500m_frac','lc_bare_500m_frac']
def fit(train_df,feature_manifest,target):
    cols=[c for c in EXPOSURE if c in train_df]; cats=[];nums=cols
    prep=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()),nums)])
    y=train_df.sample_weight.to_numpy()>.2
    if len(np.unique(y))<2:y=np.asarray(train_df.label,bool)
    model=make_pipeline(prep,LogisticRegression(C=.5,max_iter=150,class_weight='balanced',random_state=41073))
    model.fit(train_df[cols],y)
    return {'model':model,'columns':cols}
def predict(model,df):return model['model'].predict_proba(df[model['columns']])[:,1]

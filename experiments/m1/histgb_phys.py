"""Histogram gradient boosting on physical city-rank features may learn smooth transfer thresholds."""
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');cols=list(x.columns);imp=SimpleImputer(strategy='median',add_indicator=True);xx=imp.fit_transform(x)
    m=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,max_depth=3,l2_regularization=12,learning_rate=.04,random_state=92);m.fit(xx,train_df.label.astype(int),sample_weight=train_df.sample_weight)
    return {'model':m,'transform':imp,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(b['transform'].transform(x))[:,1]

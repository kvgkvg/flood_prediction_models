"""ExtraTrees on physical city-rank features may model threshold interactions with lower variance than boosting."""
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesClassifier
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');cols=list(x.columns);m=ExtraTreesClassifier(n_estimators=100,max_features=.65,min_samples_leaf=8,class_weight='balanced_subsample',n_jobs=4,random_state=191);imp=SimpleImputer(strategy='median',add_indicator=True)
    x=imp.fit_transform(x);m.fit(x,train_df.label.astype(int),sample_weight=train_df.sample_weight);return {'model':m,'transform':imp,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0)
    return b['model'].predict_proba(b['transform'].transform(x))[:,1]

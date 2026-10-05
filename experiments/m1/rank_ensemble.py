"""A rank average of linear and tree physical scorers can balance robustness and nonlinear signal."""
import numpy as np
from scipy.stats import rankdata
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from experiments.m1._util import fit_lgbm,predict_lgbm,lightgbm_frame

def fit(train_df,feature_manifest,target):
    tree=fit_lgbm(train_df,feature_manifest,'phys_cityrank');x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');cols=list(x.columns);linear=make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),LogisticRegression(C=.08,class_weight='balanced',max_iter=300,random_state=81))
    linear.fit(x,train_df.label.astype(int),logisticregression__sample_weight=train_df.sample_weight.to_numpy(float));return {'tree':tree,'linear':linear,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0);a=b['linear'].predict_proba(x)[:,1];z=predict_lgbm(b['tree'],df,{'feature_names':b['feature_names']});return .5*(rankdata(a)/len(a)+rankdata(z)/len(z))

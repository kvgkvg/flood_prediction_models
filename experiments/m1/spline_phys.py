"""Spline-binned physical city-rank inputs may capture nonlinear flood thresholds without a large tree ensemble."""
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler,KBinsDiscretizer
from sklearn.linear_model import LogisticRegression
from experiments.m1._util import lightgbm_frame

def fit(train_df,feature_manifest,target):
    x=lightgbm_frame(train_df,feature_manifest,'phys_cityrank');cols=list(x.columns);m=make_pipeline(SimpleImputer(strategy='median',add_indicator=True),KBinsDiscretizer(n_bins=5,encode='onehot',strategy='quantile'),LogisticRegression(C=.15,class_weight='balanced',max_iter=300,random_state=177))
    m.fit(x,train_df.label.astype(int),logisticregression__sample_weight=train_df.sample_weight.to_numpy(float));return {'model':m,'columns':cols,'feature_names':feature_manifest['feature_names']}
def predict(b,df):
    x=lightgbm_frame(df,{'feature_names':b['feature_names']},'phys_cityrank').reindex(columns=b['columns'],fill_value=0);return b['model'].predict_proba(x)[:,1]

"""Regularized logistic regression on the design section 4.2 inputs."""
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from experiments.m1._util import design_frame

def fit(train_df,feature_manifest,target):
    x=design_frame(train_df.drop(columns=['label','sample_weight'],errors='ignore'));model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(class_weight='balanced',max_iter=500,C=.5,random_state=41073))
    model.fit(x,train_df.label.astype(int),logisticregression__sample_weight=train_df.sample_weight.to_numpy(float))
    return {'model':model,'columns':list(x.columns)}
def predict(bundle,df):
    x=design_frame(df).reindex(columns=bundle['columns'],fill_value=0);return bundle['model'].predict_proba(x)[:,1]

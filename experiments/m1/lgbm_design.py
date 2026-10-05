"""Small strongly regularized LightGBM on design section 4.2 inputs."""
from experiments.m1._util import fit_lgbm,predict_lgbm
def fit(train_df,feature_manifest,target):return fit_lgbm(train_df,feature_manifest,'design')
def predict(model,df):return predict_lgbm(model,df,{'feature_names':model['feature_names']})

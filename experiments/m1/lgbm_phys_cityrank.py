"""LightGBM on city-rank terrain, water and non-built-up land cover only."""
from experiments.m1._util import fit_lgbm,predict_lgbm
def fit(train_df,feature_manifest,target):return fit_lgbm(train_df,feature_manifest,'phys_cityrank')
def predict(model,df):return predict_lgbm(model,df,{'feature_names':model['feature_names']})

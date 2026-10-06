# Combination v2 FIT thresholds and trade-offs

Route levels use A=top 5%, B=next 15%, C=rest. For each cause, FIT-only T thresholds define quiet (T<t_lo), watch (t_lo<=T<t_hi), alert (T>=t_hi). High=alert+A; medium=alert+B or watch+A. The requested FIT goals are alert coverage >=70% of positive days and quiet coverage >=80% of rainy-season no-report days. Threshold curves use FIT days only; DEV was not used for selection.

This replaces quantiles of P over FIT flood-day route vectors. The old rule used different population cutoffs: HCMC all-route medium=0.0449 versus in-universe=0.4033; the 44 matched in-universe DEV routes had max P=0.0709 (zero above the universe cutoff), while 11 crossed the all-route cutoff. OOU routes did not have higher P (one matched OOU route, P=0; OOU route-day p95=0). HCMC DEV positive T maxima were 0.068 rain and 0.061 tide versus FIT positive maxima 0.153 and 0.911.

## ho_chi_minh

| Cause | t_lo | t_hi | FIT positives | FIT rainy-season no-report days | Alert sensitivity | Quiet specificity | Both goals met? |
|---|---:|---:|---:|---:|---:|---:|---|
| rain | 0.00548661 | 0.01042 | 30 | 4448 | 50.0% | 56.3% | no |
| tide | 0.571892 | 0.581134 | 25 | 4448 | 72.0% | 95.9% | yes |

### rain: threshold trade-off (sampled points; full empirical curve is in `models/combination_thresholds.json`)

| t_hi | t_lo giving best quiet coverage with minimum gap | Positive days alerted | No-report days quiet |
|---:|---:|---:|---:|
| 8.02899e-05 | -0.00485308 | 100.0% | 0.0% |
| 0.00115283 | -0.00378054 | 100.0% | 0.0% |
| 0.00191936 | -0.00301401 | 100.0% | 0.0% |
| 0.0026563 | -0.00227707 | 93.3% | 0.0% |
| 0.00327797 | -0.0016554 | 90.0% | 0.0% |
| 0.0040068 | -0.000926568 | 86.7% | 0.0% |
| 0.00493313 | -2.42012e-07 | 86.7% | 0.0% |
| 0.006374 | 0.00144063 | 70.0% | 10.8% |
| 0.00866655 | 0.00373317 | 60.0% | 38.3% |
| 0.0126573 | 0.00772391 | 40.0% | 71.9% |
| 0.493417 | 0.488484 | 0.0% | 100.0% |

### tide: threshold trade-off (sampled points; full empirical curve is in `models/combination_thresholds.json`)

| t_hi | t_lo giving best quiet coverage with minimum gap | Positive days alerted | No-report days quiet |
|---:|---:|---:|---:|
| 2.3497e-21 | -0.00924142 | 100.0% | 0.0% |
| 2.93283e-18 | -0.00924142 | 100.0% | 0.0% |
| 2.19929e-15 | -0.00924142 | 100.0% | 0.0% |
| 1.13791e-12 | -0.00924142 | 96.0% | 0.0% |
| 3.27119e-10 | -0.00924142 | 92.0% | 0.0% |
| 4.22003e-08 | -0.00924138 | 92.0% | 0.0% |
| 2.2212e-06 | -0.0092392 | 92.0% | 0.0% |
| 9.17677e-05 | -0.00914965 | 88.0% | 0.0% |
| 0.00479246 | -0.00444895 | 88.0% | 0.0% |
| 0.201541 | 0.1923 | 80.0% | 92.4% |
| 0.924142 | 0.9149 | 0.0% | 99.8% |

## da_nang

| Cause | t_lo | t_hi | FIT positives | FIT rainy-season no-report days | Alert sensitivity | Quiet specificity | Both goals met? |
|---|---:|---:|---:|---:|---:|---:|---|
| rain | 0.792619 | 0.801861 | 1 | 2561 | 100.0% | 97.8% | yes |
| tide | 1 | 1 | 0 | 2561 | 0.0% | 0.0% | no |

### rain: threshold trade-off (sampled points; full empirical curve is in `models/combination_thresholds.json`)

| t_hi | t_lo giving best quiet coverage with minimum gap | Positive days alerted | No-report days quiet |
|---:|---:|---:|---:|
| 3.67555e-20 | -0.00924142 | 100.0% | 0.0% |
| 9.47936e-19 | -0.00924142 | 100.0% | 0.0% |
| 6.13291e-17 | -0.00924142 | 100.0% | 0.0% |
| 7.6812e-15 | -0.00924142 | 100.0% | 0.0% |
| 8.87827e-13 | -0.00924142 | 100.0% | 0.0% |
| 6.22414e-11 | -0.00924142 | 100.0% | 0.0% |
| 7.19413e-09 | -0.00924141 | 100.0% | 0.0% |
| 1.37096e-06 | -0.00924005 | 100.0% | 0.0% |
| 0.000230507 | -0.00901091 | 100.0% | 0.0% |
| 0.0293122 | 0.0200708 | 100.0% | 87.1% |
| 0.924142 | 0.9149 | 0.0% | 99.9% |

### tide: threshold trade-off (sampled points; full empirical curve is in `models/combination_thresholds.json`)

| t_hi | t_lo giving best quiet coverage with minimum gap | Positive days alerted | No-report days quiet |
|---:|---:|---:|---:|
| no FIT positive days | — | — | — |

HCMC rain cannot meet both targets with the selected task-5 trigger and this rain source; its fitted compromise is shown above. Da Nang rain meets the arithmetic targets with only one FIT positive day, so the apparent 100% sensitivity is not a reliable estimate. Da Nang tide has no positives and is deliberately kept quiet.

M1 refit used `lgbm_phys_cityrank`, in-universe routes, all positive/known-report routes, and a fixed-seed cap of 20,000 unlabeled routes per city. City-relative score for OOU routes is half their in-universe-reference percentile; a route with FIT history gets S_hist=0.80+0.20*min(1,n_distinct_dates/3), then S_hyb=max(S_model,S_hist).

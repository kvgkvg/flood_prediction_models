# Model card — flood-risk routes, pre-test freeze

## Models and data

Model 1 estimates persistent route susceptibility S with `lgbm_phys_cityrank`, using terrain, water proximity, and non-built-up land-cover city-rank features. It is fit on official IRD observations in HCMC and citizen reports in Da Nang, treating unlabeled routes as negatives with a fixed cap of 20,000 sampled routes/city. Route history is retained as a separate high-priority term.

The shared rain trigger is a regularized logistic model on city/source CDF percentiles for daily maximum 3-hour rain and daily total. Its coefficients are fit from pooled pre-2023 FIT days using ERA5 percentile inputs. Live/test input is IFS percentiles with ERA5 fallback. The tide trigger remains the earlier HCMC astronomical-tide percentile model; Da Nang has no tide labels.

## Evidence before the locked test

Model 1 transfer baseline: `lgbm_phys_cityrank` PRIMARY **0.331 [0.299, 0.371]**, HEADLINE **0.458 [0.421, 0.498]**. Exposure-only baseline PRIMARY **0.124 [0.094, 0.152]**, HEADLINE **0.219 [0.194, 0.263]**. Other baseline rankings and intervals are in `reports/m1_leaderboard.md`.

Shared percentile rain model selected max-3h + daily-total percentiles; leave-one-year-out mean AUC was **0.772** across nine estimable years. The fixed DEV trigger on IFS percentiles had AUC HCMC **0.705 [0.529, 0.870]** and Da Nang **0.758 [0.658, 0.856]**; rain shares and ERA5-input comparison are in `reports/percentile_trigger_dev.md`. The A4 FIT threshold target was not fully met: alert captured 57.1% of FIT flood days while 85.1% of rainy-season no-report days stayed quiet; watch-or-alert captured 85.7%.

On IFS-driven DEV, HCMC had 46 records / 6 days and Da Nang 126 / 16 days. In-universe D1 model/history/hybrid were HCMC **.203 [.067,.342] / .288 [.096,.583] / .217 [.067,.383]**, Da Nang **.210 [.076,.366] / .097 [0,.222] / .097 [0,.222]**. In-universe D2 top-5% hit rates model/history/hybrid were HCMC **.482/.288/.510**, Da Nang **.367/.097/.316**; at top-20% they were HCMC **.679/.288/.679**, Da Nang **.903/.097/.903**. Full paired intervals, NEW-route results, D3 alert burden, and D6 record capture are in `reports/dev_eval_ifs.md` and `reports/dev_eval_era5.md`.

The fixed hybrid exactly preserves history hit rate at K=history size. The requested model-floor check fails for Da Nang in-universe at 5% (hybrid-model hit-rate delta **−.051**); this is a real conflict between fixed history priority and the new-route ranking, not an interval artifact.

## Biases and limits

- HCMC IRD and press-style reporting overrepresent named major roads; road class had strong raw single-feature performance in earlier work.
- Da Nang citizen reports concentrate in dense residential areas and one FIT event (2022-10-14) dominates its early label history.
- ERA5 is coarse (~0.25°, about 28 km); IFS is nominally 9 km. The shared percentile mapping helps harmonize distributions but cannot create local storm detail.
- Tide is only empirically verifiable in HCMC; the Da Nang tide model has no positive labels.
- Unreported routes/days are not confirmed dry. The locked 2025+ set has not been accessed.

These data do not prove calibration, causal hydrologic susceptibility, operational lead-time skill, or generalization to the locked period. DEV is small, event-based, and affected by reporting practices. Section 7 metrics measure ranking/capture under the recorded label process, not flood probability truth.

## Locked test (opened 2026-10-06; scoring replayed during bug fixes)

The frozen model/config was evaluated against 2025-01-01 through 2026-10-05 input availability. Two report/coverage bug fixes required rerunning the scoring path before the final tables were produced; the frozen model, config, thresholds, and evaluation rules did not change, and no result-driven tuning followed. This means the test was opened once for this task but its scoring computation was replayed. Two report/coverage bug fixes required rerunning the scoring path before the final tables were produced; the frozen model, config, thresholds, and evaluation rules did not change, and no result-driven tuning followed. This means the test was opened once for this task but its scoring computation was replayed. There were 33 dated HCMC records across 8 days (all 33 matched) and 115 dated Da Nang records across 18 days (86 matched; 29 unmatched). HCMC also has 17 year-known/date-missing rows: 14 matched and used only for D6 ranking; 3 unmatched. Rain IFS CDF references ended 2024-12-31; no locked days entered the reference CDF or any fit.

In-universe D1 hybrid/model/history hit rates were HCMC **0.208 [0.000, 0.500] / 0.167 [0.000, 0.417] / 0.383 [0.208, 0.529]** and Da Nang **0.321 [0.169, 0.498] / 0.384 [0.217, 0.560] / 0.177 [0.058, 0.327]**. At a 5% budget, in-universe hybrid D2 hit rates were HCMC **0.733 [0.510, 0.927]** and Da Nang **0.277 [0.131, 0.455]**; D6 top-5 capture was **0.733 [0.510, 0.927]** and **0.271 [0.125, 0.451]** respectively. Dated-only measures exclude unmatched Da Nang records.

IFS rain-trigger AUC was HCMC **0.635 [0.543, 0.749]** over 6 rain-record days and Da Nang **0.906 [0.852, 0.955]** over 18. HCMC astronomical-tide trigger AUC was **0.876 [0.733, 0.998]** over 3 tide-record days. In-universe hybrid dry-season medium/high burden was HCMC **0.018 [0.012, 0.024]** and Da Nang **0.013 [0.011, 0.016]**. Detailed D1–D4, D6, D7, and side-by-side DEV values are in `reports/locked_eval.md`.

This held-out result supports promising route ranking in Da Nang, but the D1 alert hit rate is modest, HCMC intervals are broad, and 29 Da Nang records were unmatched. HCMC's history baseline beat the model on rain-labeled days. The trigger alert state caught 44.4% of Da Nang flood days but none of the eight HCMC days; tide state caught one of three HCMC tide days. These data do not establish calibrated probabilities, absence of flooding on unreported roads, hourly forecast skill, lead time, or deployment safety. The test was opened for this evaluation; no future tuning should use it.

# Model 1 v2 experiment leaderboard

Reproduce baseline refresh: `PYTHONPATH=src .venv/bin/python scripts/eval_m1.py --scorer all --tasks T1,T2,T3 --n-boot 100`; reproduce this report with `PYTHONPATH=src .venv/bin/python scripts/make_m1_report.py`. A 100-draw refresh was used for all rows; paired candidate comparisons also used 100 draws. All labels are train/train_undated only. Locked records were not loaded.

PRIMARY is the mean propensity-stratified recall@10 over T1–T3. HEADLINE is road-class-stratified recall@10 and HEADLINE2 further stratifies by built-up tercile. Each reported PRIMARY and HEADLINE interval is a joint route bootstrap over the three tasks. `vs_best` is paired PRIMARY delta and interval versus the current best at experiment time.

| Rank | Scorer | Decision | PRIMARY [95% CI] | HEADLINE [95% CI] | HEADLINE2 | vs_best PRIMARY delta [95% CI], P | Runtime s |
|---:|---|---|---:|---:|---:|---|---:|
| 1 | lgbm_phys_cityrank | baseline | 0.331 [0.299, 0.371] | 0.458 [0.421, 0.498] | 0.364 |  | 15.4 |
| 2 | lgbm_all | baseline | 0.321 [0.282, 0.355] | 0.497 [0.459, 0.536] | 0.400 |  | 15.7 |
| 3 | lgbm_all_cityrank | baseline | 0.304 [0.276, 0.337] | 0.463 [0.434, 0.503] | 0.382 |  | 15.8 |
| 4 | rank_ensemble | discard | 0.303 [0.269, 0.339] | 0.431 [0.394, 0.464] | 0.365 | -0.02676 [-0.06147,0.00069],P=0.030 | 28.1 |
| 5 | shallow_phys | discard | 0.301 [0.274, 0.346] | 0.418 [0.391, 0.463] | 0.347 | -0.03191 [-0.05917,-0.00966],P=0.000 | 12.3 |
| 6 | pu_bagging | discard | 0.300 [0.271, 0.332] | 0.433 [0.396, 0.471] | 0.370 | -0.03048 [-0.06413,-0.00362],P=0.010 | 14.8 |
| 7 | terrain_water_only | discard | 0.298 [0.264, 0.331] | 0.408 [0.372, 0.443] | 0.345 | -0.03304 [-0.05982,-0.00595],P=0.010 | 15.2 |
| 8 | monotone_phys | discard | 0.292 [0.268, 0.334] | 0.440 [0.414, 0.477] | 0.362 | -0.03712 [-0.06782,-0.00352],P=0.010 | 16.2 |
| 9 | extratrees_phys | discard | 0.285 [0.256, 0.326] | 0.398 [0.358, 0.440] | 0.330 | -0.04451 [-0.06988,-0.01272],P=0.010 | 41.4 |
| 10 | histgb_phys | discard | 0.285 [0.259, 0.321] | 0.423 [0.382, 0.460] | 0.336 | -0.04534 [-0.06982,-0.02454],P=0.000 | 73.6 |
| 11 | exposure_nuisance | discard | 0.282 [0.251, 0.326] | 0.327 [0.300, 0.374] | 0.335 | -0.04718 [-0.08059,-0.01375],P=0.000 | 15.9 |
| 12 | logreg_phys_cityrank | discard | 0.270 [0.237, 0.306] | 0.390 [0.353, 0.420] | 0.326 | -0.05909 [-0.09949,-0.03416],P=0.000 | 25.3 |
| 13 | spline_phys | discard | 0.267 [0.236, 0.303] | 0.323 [0.291, 0.360] | 0.300 | -0.06085 [-0.10504,-0.01689],P=0.000 | 26.7 |
| 14 | lgbm_design | baseline | 0.247 [0.208, 0.290] | 0.353 [0.315, 0.387] | 0.265 |  | 12.5 |
| 15 | exposure_matched | discard | 0.242 [0.211, 0.275] | 0.282 [0.255, 0.317] | 0.268 | -0.08708 [-0.12120,-0.04755],P=0.000 | 11.9 |
| 16 | compact_fab | discard | 0.230 [0.197, 0.262] | 0.373 [0.335, 0.410] | 0.289 | -0.09695 [-0.13042,-0.05439],P=0.000 | 12.0 |
| 17 | logreg_design | baseline | 0.218 [0.175, 0.249] | 0.391 [0.351, 0.420] | 0.301 |  | 17.4 |
| 18 | near_water | baseline | 0.171 [0.145, 0.198] | 0.158 [0.141, 0.179] | 0.201 |  | 8.0 |
| 19 | elev_low | baseline | 0.154 [0.125, 0.182] | 0.125 [0.099, 0.147] | 0.168 |  | 13.3 |
| 20 | exposure_only | baseline | 0.124 [0.094, 0.152] | 0.219 [0.194, 0.263] | 0.210 |  | 14.8 |
| 21 | random | baseline | 0.098 [0.076, 0.123] | 0.096 [0.074, 0.123] | 0.095 |  | 10.8 |
| 22 | road_class | baseline | 0.088 [0.073, 0.104] | 0.056 [0.046, 0.064] | 0.078 |  | 9.1 |
| 23 | builtup | baseline | 0.079 [0.064, 0.097] | 0.171 [0.147, 0.192] | 0.092 |  | 8.1 |

## T1: HCMC → Da Nang rain

| Scorer | Decision | Propensity recall@10 | Propensity AUC | Urban recall@10 | Road-class strat recall@10 | Raw recall@10 |
|---|---|---:|---:|---:|---:|---:|
| lgbm_phys_cityrank | baseline | 0.253 [0.218, 0.295] | 0.700 [0.677, 0.726] | 0.374 | 0.422 | 0.462 |
| lgbm_all | baseline | 0.197 [0.162, 0.235] | 0.654 [0.620, 0.682] | 0.295 | 0.438 | 0.415 |
| lgbm_all_cityrank | baseline | 0.167 [0.135, 0.206] | 0.657 [0.632, 0.684] | 0.278 | 0.418 | 0.423 |
| rank_ensemble | discard | 0.256 [0.216, 0.296] | 0.686 [0.662, 0.711] | 0.363 | 0.420 | 0.456 |
| shallow_phys | discard | 0.251 [0.214, 0.294] | 0.683 [0.660, 0.709] | 0.363 | 0.429 | 0.481 |
| pu_bagging | discard | 0.248 [0.208, 0.305] | 0.670 [0.649, 0.697] | 0.374 | 0.433 | 0.471 |
| terrain_water_only | discard | 0.263 [0.228, 0.311] | 0.700 [0.679, 0.727] | 0.336 | 0.400 | 0.433 |
| monotone_phys | discard | 0.172 [0.143, 0.208] | 0.635 [0.609, 0.661] | 0.251 | 0.395 | 0.380 |
| extratrees_phys | discard | 0.230 [0.191, 0.267] | 0.636 [0.606, 0.663] | 0.284 | 0.359 | 0.365 |
| histgb_phys | discard | 0.251 [0.211, 0.289] | 0.683 [0.660, 0.711] | 0.365 | 0.413 | 0.468 |
| exposure_nuisance | discard | 0.200 [0.158, 0.237] | 0.653 [0.627, 0.683] | 0.231 | 0.194 | 0.228 |
| logreg_phys_cityrank | discard | 0.228 [0.190, 0.266] | 0.653 [0.629, 0.680] | 0.316 | 0.395 | 0.425 |
| spline_phys | discard | 0.192 [0.162, 0.229] | 0.636 [0.612, 0.667] | 0.246 | 0.220 | 0.266 |
| lgbm_design | baseline | 0.170 [0.133, 0.204] | 0.612 [0.577, 0.640] | 0.272 | 0.306 | 0.319 |
| exposure_matched | discard | 0.190 [0.153, 0.231] | 0.634 [0.609, 0.660] | 0.251 | 0.208 | 0.246 |
| compact_fab | discard | 0.147 [0.115, 0.182] | 0.584 [0.554, 0.620] | 0.225 | 0.316 | 0.261 |
| logreg_design | baseline | 0.144 [0.111, 0.180] | 0.603 [0.577, 0.631] | 0.257 | 0.311 | 0.304 |
| near_water | baseline | 0.147 [0.105, 0.181] | 0.561 [0.531, 0.588] | 0.170 | 0.099 | 0.106 |
| elev_low | baseline | 0.122 [0.088, 0.149] | 0.559 [0.534, 0.577] | 0.102 | 0.056 | 0.063 |
| exposure_only | baseline | 0.114 [0.080, 0.147] | 0.565 [0.537, 0.598] | 0.254 | 0.200 | 0.266 |
| random | baseline | 0.091 [0.067, 0.118] | 0.500 [0.475, 0.523] | 0.096 | 0.086 | 0.086 |
| road_class | baseline | 0.101 [0.073, 0.125] | 0.531 [0.505, 0.554] | 0.187 | 0.039 | 0.172 |
| builtup | baseline | 0.091 [0.067, 0.119] | 0.558 [0.527, 0.584] | 0.193 | 0.302 | 0.303 |

## T2: Da Nang → HCMC rain

| Scorer | Decision | Propensity recall@10 | Propensity AUC | Urban recall@10 | Road-class strat recall@10 | Raw recall@10 |
|---|---|---:|---:|---:|---:|---:|
| lgbm_phys_cityrank | baseline | 0.315 [0.267, 0.379] | 0.726 [0.691, 0.762] | 0.506 | 0.376 | 0.624 |
| lgbm_all | baseline | 0.309 [0.255, 0.365] | 0.736 [0.703, 0.766] | 0.588 | 0.410 | 0.691 |
| lgbm_all_cityrank | baseline | 0.281 [0.222, 0.346] | 0.721 [0.691, 0.756] | 0.518 | 0.348 | 0.629 |
| rank_ensemble | discard | 0.230 [0.160, 0.292] | 0.709 [0.678, 0.741] | 0.494 | 0.324 | 0.601 |
| shallow_phys | discard | 0.236 [0.185, 0.295] | 0.707 [0.673, 0.741] | 0.429 | 0.309 | 0.556 |
| pu_bagging | discard | 0.247 [0.188, 0.306] | 0.712 [0.677, 0.744] | 0.418 | 0.343 | 0.545 |
| terrain_water_only | discard | 0.258 [0.194, 0.315] | 0.704 [0.669, 0.736] | 0.512 | 0.315 | 0.551 |
| monotone_phys | discard | 0.287 [0.230, 0.363] | 0.727 [0.695, 0.760] | 0.524 | 0.343 | 0.607 |
| extratrees_phys | discard | 0.242 [0.191, 0.301] | 0.696 [0.660, 0.733] | 0.476 | 0.298 | 0.556 |
| histgb_phys | discard | 0.247 [0.197, 0.315] | 0.707 [0.676, 0.743] | 0.465 | 0.326 | 0.567 |
| exposure_nuisance | discard | 0.236 [0.191, 0.298] | 0.691 [0.659, 0.727] | 0.559 | 0.264 | 0.556 |
| logreg_phys_cityrank | discard | 0.219 [0.154, 0.281] | 0.677 [0.644, 0.707] | 0.424 | 0.258 | 0.506 |
| spline_phys | discard | 0.225 [0.180, 0.279] | 0.672 [0.640, 0.708] | 0.400 | 0.258 | 0.500 |
| lgbm_design | baseline | 0.219 [0.154, 0.287] | 0.669 [0.624, 0.702] | 0.435 | 0.309 | 0.472 |
| exposure_matched | discard | 0.185 [0.132, 0.242] | 0.642 [0.607, 0.683] | 0.406 | 0.242 | 0.410 |
| compact_fab | discard | 0.213 [0.163, 0.289] | 0.663 [0.627, 0.703] | 0.506 | 0.287 | 0.545 |
| logreg_design | baseline | 0.152 [0.104, 0.216] | 0.652 [0.607, 0.690] | 0.665 | 0.337 | 0.758 |
| near_water | baseline | 0.107 [0.064, 0.140] | 0.525 [0.491, 0.558] | 0.212 | 0.104 | 0.160 |
| elev_low | baseline | 0.090 [0.051, 0.124] | 0.554 [0.519, 0.589] | 0.153 | 0.084 | 0.124 |
| exposure_only | baseline | 0.079 [0.042, 0.115] | 0.629 [0.595, 0.657] | 0.288 | 0.140 | 0.427 |
| random | baseline | 0.096 [0.051, 0.135] | 0.491 [0.446, 0.532] | 0.106 | 0.101 | 0.096 |
| road_class | baseline | 0.090 [0.053, 0.132] | 0.587 [0.559, 0.621] | 0.706 | 0.044 | 0.734 |
| builtup | baseline | 0.112 [0.070, 0.152] | 0.634 [0.598, 0.668] | 0.118 | 0.154 | 0.225 |

## T3: HCMC tide, spatial blocks

| Scorer | Decision | Propensity recall@10 | Propensity AUC | Urban recall@10 | Road-class strat recall@10 | Raw recall@10 |
|---|---|---:|---:|---:|---:|---:|
| lgbm_phys_cityrank | baseline | 0.424 [0.344, 0.497] | 0.819 [0.794, 0.843] | 0.667 | 0.576 | 0.662 |
| lgbm_all | baseline | 0.457 [0.358, 0.523] | 0.829 [0.804, 0.852] | 0.756 | 0.642 | 0.748 |
| lgbm_all_cityrank | baseline | 0.464 [0.377, 0.533] | 0.829 [0.805, 0.853] | 0.780 | 0.623 | 0.755 |
| rank_ensemble | discard | 0.424 [0.351, 0.494] | 0.836 [0.814, 0.859] | 0.715 | 0.550 | 0.728 |
| shallow_phys | discard | 0.417 [0.348, 0.507] | 0.796 [0.771, 0.823] | 0.610 | 0.517 | 0.603 |
| pu_bagging | discard | 0.404 [0.338, 0.480] | 0.793 [0.766, 0.824] | 0.634 | 0.523 | 0.616 |
| terrain_water_only | discard | 0.371 [0.298, 0.460] | 0.809 [0.784, 0.836] | 0.659 | 0.510 | 0.642 |
| monotone_phys | discard | 0.417 [0.344, 0.507] | 0.823 [0.800, 0.844] | 0.772 | 0.583 | 0.742 |
| extratrees_phys | discard | 0.384 [0.308, 0.464] | 0.766 [0.727, 0.800] | 0.618 | 0.537 | 0.623 |
| histgb_phys | discard | 0.358 [0.295, 0.424] | 0.802 [0.776, 0.827] | 0.659 | 0.530 | 0.636 |
| exposure_nuisance | discard | 0.411 [0.331, 0.490] | 0.817 [0.790, 0.843] | 0.659 | 0.523 | 0.656 |
| logreg_phys_cityrank | discard | 0.364 [0.301, 0.430] | 0.822 [0.799, 0.844] | 0.659 | 0.517 | 0.689 |
| spline_phys | discard | 0.384 [0.318, 0.477] | 0.793 [0.771, 0.825] | 0.553 | 0.490 | 0.603 |
| lgbm_design | baseline | 0.351 [0.281, 0.437] | 0.774 [0.744, 0.809] | 0.675 | 0.444 | 0.656 |
| exposure_matched | discard | 0.351 [0.281, 0.434] | 0.787 [0.757, 0.816] | 0.545 | 0.397 | 0.510 |
| compact_fab | discard | 0.331 [0.265, 0.397] | 0.796 [0.769, 0.824] | 0.707 | 0.517 | 0.702 |
| logreg_design | baseline | 0.358 [0.265, 0.428] | 0.805 [0.778, 0.832] | 0.740 | 0.523 | 0.728 |
| near_water | baseline | 0.258 [0.195, 0.338] | 0.749 [0.718, 0.780] | 0.480 | 0.272 | 0.367 |
| elev_low | baseline | 0.252 [0.179, 0.318] | 0.750 [0.729, 0.777] | 0.293 | 0.236 | 0.278 |
| exposure_only | baseline | 0.179 [0.119, 0.238] | 0.593 [0.548, 0.636] | 0.642 | 0.318 | 0.675 |
| random | baseline | 0.106 [0.066, 0.159] | 0.479 [0.432, 0.531] | 0.089 | 0.099 | 0.099 |
| road_class | baseline | 0.073 [0.033, 0.103] | 0.512 [0.472, 0.542] | 0.520 | 0.084 | 0.532 |
| builtup | baseline | 0.033 [0.013, 0.073] | 0.438 [0.401, 0.473] | 0.024 | 0.058 | 0.073 |

## What worked, what did not, and why

- The prior best remained `lgbm_phys_cityrank` (PRIMARY 0.331), with terrain, water and non-built-up land cover ranked by city. None of the 12 candidates met both P(new > best) ≥ 0.90 and HEADLINE drop ≤ 0.01.
- PU bagging, exposure-matched negative sampling, exposure nuisance replacement, monotone constraints, compact features, physical logistic/spline models, rank averaging, shallow boosting, ExtraTrees, histogram boosting, and terrain/water-only all lost paired PRIMARY. Matching on exposure likely discarded useful physical contrasts as well as nuisance structure; compact/linear/tree alternatives did not recover a stable transfer gain at this label volume.
- The exposure-only baseline had PRIMARY 0.124, well below the physical best, but raw HEADLINE 0.219 shows appreciable reporting structure remains. Propensity control does not remove all exposure/label noise.

## Assumptions and skipped ideas

- Exposure outcome is whether a route has an eligible training/undated report (`n_records` present); the 5-fold logistic propensity model is cross-fitted over the evaluated city universe using only exposure variables. Deciles define the strata.
- `exposure_only` predicts that exposure outcome from the same allowed exposure predictors.
- Cross-city stable feature filtering was skipped because it requires label-informed agreement in the target city, which would leak test labels. Date-count weighting was skipped because the frozen scorer interface does not expose `n_distinct_dates`. New feature engineering was skipped to preserve the fixed feature inputs.
- Per-task intervals use stratified route bootstrap. PRIMARY and HEADLINE intervals are joint across T1–T3. This is descriptive baseline evidence only; no locked data was evaluated.

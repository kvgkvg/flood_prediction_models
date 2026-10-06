# Model 2/combination DEV rehearsal

All DEV summaries use dated unlocked records from 2023–2024; 2025+ records were predicate-filtered out before attributes were read. Intervals resample flood days. Route-day risk is computed in a per-day loop; no route × calendar-day matrix is constructed. A hit means a matched DEV flood route is selected. Unmatched reports are excluded from route hit rates and counted below.

M1 refit: lgbm_phys_cityrank; in-universe routes only; all positive and known-report routes retained; fixed-seed unlabeled subsample capped at 20,000 per city. Numeric model inputs are float32 and LightGBM used two threads.

## ho_chi_minh

DEV records: 46 on 6 distinct dates; flood days with any dated record: 6; records unmatched to routes: 0.

| Scope | days | D1 P | D1 history | D1 hybrid | NEW P | NEW history | NEW hybrid | D4 AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 6 | 0.267 [0.000, 0.600] | 0.283 [0.092, 0.583] | 0.267 [0.000, 0.600] | 0.320 [0.000, 0.720] | 0.000 [0.000, 0.000] | 0.320 [0.000, 0.720] | 0.570 [0.420, 0.727] |
| in_universe | 6 | 0.000 [0.000, 0.000] | 0.288 [0.096, 0.583] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.458 [0.448, 0.468] |

Equal route budget hit rate (mean [95% flood-day bootstrap CI]):

| Scope / budget | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / K=history count | 0.283 [0.092, 0.583] | 0.087 [0.032, 0.141] | 0.087 [0.032, 0.141] |
| all / K=5% | 0.283 [0.092, 0.583] | 0.599 [0.413, 0.792] | 0.599 [0.413, 0.792] |
| all / K=20% | 0.357 [0.142, 0.628] | 0.904 [0.844, 0.965] | 0.904 [0.844, 0.965] |
| in_universe / K=history count | 0.288 [0.096, 0.583] | 0.089 [0.035, 0.143] | 0.089 [0.035, 0.143] |
| in_universe / K=5% | 0.288 [0.096, 0.583] | 0.482 [0.319, 0.706] | 0.482 [0.319, 0.706] |
| in_universe / K=20% | 0.343 [0.131, 0.621] | 0.714 [0.575, 0.854] | 0.714 [0.575, 0.854] |

Same equal-budget hits restricted to DEV-positive routes with no FIT route history (history-only is zero by definition):

| Scope / budget | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / K=history count | 0.000 [0.000, 0.000] | 0.062 [0.000, 0.142] | 0.062 [0.000, 0.142] |
| all / K=5% | 0.000 [0.000, 0.000] | 0.450 [0.280, 0.619] | 0.450 [0.280, 0.619] |
| all / K=20% | 0.000 [0.000, 0.000] | 0.865 [0.803, 0.938] | 0.865 [0.803, 0.938] |
| in_universe / K=history count | 0.000 [0.000, 0.000] | 0.062 [0.000, 0.142] | 0.062 [0.000, 0.142] |
| in_universe / K=5% | 0.000 [0.000, 0.000] | 0.292 [0.207, 0.371] | 0.292 [0.207, 0.371] |
| in_universe / K=20% | 0.000 [0.000, 0.000] | 0.605 [0.474, 0.737] | 0.605 [0.474, 0.737] |

Alert burden, share of routes at medium/high (mean [95% day bootstrap CI]):

| Scope / day type | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / DEV record days | 0.002 [0.002, 0.002] | 0.054 [0.000, 0.109] | 0.054 [0.000, 0.109] |
| all / rainy-season no-record days | 0.002 [0.002, 0.002] | 0.050 [0.039, 0.063] | 0.050 [0.039, 0.063] |
| all / dry-season days | 0.002 [0.002, 0.002] | 0.065 [0.049, 0.082] | 0.065 [0.049, 0.082] |
| in_universe / DEV record days | 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| in_universe / rainy-season no-record days | 0.004 [0.004, 0.004] | 0.030 [0.020, 0.041] | 0.030 [0.020, 0.041] |
| in_universe / dry-season days | 0.004 [0.004, 0.004] | 0.031 [0.020, 0.044] | 0.031 [0.020, 0.044] |

Alert burden restricted to routes without any FIT history:

| Scope / day type | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / DEV record days | 0.000 [0.000, 0.000] | 0.054 [0.000, 0.108] | 0.054 [0.000, 0.108] |
| all / rainy-season no-record days | 0.000 [0.000, 0.000] | 0.050 [0.038, 0.062] | 0.050 [0.038, 0.062] |
| all / dry-season days | 0.000 [0.000, 0.000] | 0.065 [0.049, 0.082] | 0.065 [0.049, 0.082] |
| in_universe / DEV record days | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| in_universe / rainy-season no-record days | 0.000 [0.000, 0.000] | 0.030 [0.019, 0.040] | 0.030 [0.019, 0.040] |
| in_universe / dry-season days | 0.000 [0.000, 0.000] | 0.031 [0.020, 0.043] | 0.031 [0.020, 0.043] |

## da_nang

DEV records: 126 on 16 distinct dates; flood days with any dated record: 16; records unmatched to routes: 0.

| Scope | days | D1 P | D1 history | D1 hybrid | NEW P | NEW history | NEW hybrid | D4 AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 16 | 0.016 [0.000, 0.047] | 0.095 [0.000, 0.222] | 0.016 [0.000, 0.047] | 0.017 [0.000, 0.050] | 0.000 [0.000, 0.000] | 0.017 [0.000, 0.050] | 0.523 [0.488, 0.589] |
| in_universe | 16 | 0.021 [0.000, 0.062] | 0.097 [0.000, 0.222] | 0.021 [0.000, 0.062] | 0.022 [0.000, 0.067] | 0.000 [0.000, 0.000] | 0.022 [0.000, 0.067] | 0.527 [0.492, 0.591] |

Equal route budget hit rate (mean [95% flood-day bootstrap CI]):

| Scope / budget | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / K=history count | 0.095 [0.000, 0.222] | 0.072 [0.000, 0.172] | 0.072 [0.000, 0.172] |
| all / K=5% | 0.095 [0.000, 0.222] | 0.170 [0.034, 0.340] | 0.170 [0.034, 0.340] |
| all / K=20% | 0.095 [0.000, 0.222] | 0.422 [0.204, 0.641] | 0.422 [0.204, 0.641] |
| in_universe / K=history count | 0.097 [0.000, 0.222] | 0.073 [0.000, 0.176] | 0.073 [0.000, 0.176] |
| in_universe / K=5% | 0.097 [0.000, 0.222] | 0.162 [0.030, 0.330] | 0.162 [0.030, 0.330] |
| in_universe / K=20% | 0.097 [0.000, 0.222] | 0.415 [0.208, 0.631] | 0.415 [0.208, 0.631] |

Same equal-budget hits restricted to DEV-positive routes with no FIT route history (history-only is zero by definition):

| Scope / budget | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / K=history count | 0.000 [0.000, 0.000] | 0.058 [0.000, 0.161] | 0.058 [0.000, 0.161] |
| all / K=5% | 0.000 [0.000, 0.000] | 0.162 [0.025, 0.339] | 0.162 [0.025, 0.339] |
| all / K=20% | 0.000 [0.000, 0.000] | 0.445 [0.211, 0.678] | 0.445 [0.211, 0.678] |
| in_universe / K=history count | 0.000 [0.000, 0.000] | 0.058 [0.000, 0.161] | 0.058 [0.000, 0.161] |
| in_universe / K=5% | 0.000 [0.000, 0.000] | 0.151 [0.023, 0.323] | 0.151 [0.023, 0.323] |
| in_universe / K=20% | 0.000 [0.000, 0.000] | 0.437 [0.200, 0.667] | 0.437 [0.200, 0.667] |

Alert burden, share of routes at medium/high (mean [95% day bootstrap CI]):

| Scope / day type | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / DEV record days | 0.016 [0.016, 0.016] | 0.012 [0.000, 0.036] | 0.012 [0.000, 0.036] |
| all / rainy-season no-record days | 0.016 [0.016, 0.016] | 0.004 [0.001, 0.007] | 0.004 [0.001, 0.007] |
| all / dry-season days | 0.016 [0.016, 0.016] | 0.001 [0.000, 0.002] | 0.001 [0.000, 0.002] |
| in_universe / DEV record days | 0.023 [0.023, 0.023] | 0.012 [0.000, 0.035] | 0.012 [0.000, 0.035] |
| in_universe / rainy-season no-record days | 0.023 [0.023, 0.023] | 0.003 [0.000, 0.005] | 0.003 [0.000, 0.005] |
| in_universe / dry-season days | 0.023 [0.023, 0.023] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

Alert burden restricted to routes without any FIT history:

| Scope / day type | History | Model P | Hybrid |
|---|---:|---:|---:|
| all / DEV record days | 0.000 [0.000, 0.000] | 0.011 [0.000, 0.034] | 0.011 [0.000, 0.034] |
| all / rainy-season no-record days | 0.000 [0.000, 0.000] | 0.004 [0.001, 0.007] | 0.004 [0.001, 0.007] |
| all / dry-season days | 0.000 [0.000, 0.000] | 0.001 [0.000, 0.001] | 0.001 [0.000, 0.001] |
| in_universe / DEV record days | 0.000 [0.000, 0.000] | 0.011 [0.000, 0.032] | 0.011 [0.000, 0.032] |
| in_universe / rainy-season no-record days | 0.000 [0.000, 0.000] | 0.002 [0.000, 0.005] | 0.002 [0.000, 0.005] |
| in_universe / dry-season days | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |


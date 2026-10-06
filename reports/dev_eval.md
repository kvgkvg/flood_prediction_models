# Combination v2 DEV evaluation

A1 diagnosis of v1 HCMC D1: FIT medium cutoffs differed by population (all routes 0.0449; in-universe 0.4033). The 44 matched in-universe DEV flood routes had max P=0.0709; none passed 0.4033, while 11 passed the lower all-route cutoff. The OOU group did not have higher P (1 matched DEV route, P=0; OOU route-day P p95=0). Driver shift compounded this: HCMC DEV positive-day max T_rain max=0.068 vs FIT positive max=0.153, and T_tide max=0.061 vs 0.911. V2 removes population-specific P quantile levels.

Levels use per-cause FIT-only T states and route bands: A top 5%, B next 15%, C rest; high=alert+A, medium=alert+B or watch+A. Model-only uses S_model; hybrid uses S_hyb=max(S_model,S_hist); history-only flags FIT routes. P_model/P_hybrid remain continuous routing-cost scores. This is a documented change from the prior flood-day-P quantile rule because that rule produced a population-dependent zero-alert failure.

Rainy-season no-report days are season days without a record of the cause. Unreported days are not confirmed dry. All DEV labels are 2023–2024; locked records were filtered out before attributes were read. Intervals bootstrap days.

## ho_chi_minh

DEV records=46; distinct report dates=6; matched event days=6; unmatched records=0.

| Scope | D1 Model | D1 History | D1 Hybrid | D1 NEW Model | D1 NEW History | D1 NEW Hybrid |
|---|---:|---:|---:|---:|---:|---:|
| all | 0.422 [0.133, 0.722] | 0.283 [0.092, 0.583] | 0.422 [0.133, 0.722] | 0.493 [0.156, 0.831] | 0.000 [0.000, 0.000] | 0.493 [0.156, 0.831] |
| in_universe | 0.339 [0.067, 0.617] | 0.288 [0.096, 0.583] | 0.339 [0.067, 0.617] | 0.391 [0.080, 0.702] | 0.000 [0.000, 0.000] | 0.391 [0.080, 0.702] |

D2 equal route-budget hit rate (K=history-list size / 5% / 20%); each cell is the ordered three-budget vector with day-bootstrap 95% CI. NEW restricts denominators to DEV routes without FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.283 [0.092, 0.583] / 0.283 [0.092, 0.583] / 0.283 [0.092, 0.583] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.087 [0.032, 0.141] / 0.599 [0.413, 0.792] / 0.904 [0.844, 0.965] | 0.062 [0.000, 0.142] / 0.450 [0.280, 0.619] / 0.865 [0.803, 0.938] |
| all | hybrid | 0.119 [0.049, 0.187] / 0.599 [0.413, 0.792] / 0.904 [0.844, 0.965] | 0.062 [0.000, 0.142] / 0.450 [0.280, 0.619] / 0.865 [0.803, 0.938] |
| in_universe | history | 0.288 [0.096, 0.583] / 0.288 [0.096, 0.583] / 0.288 [0.096, 0.583] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.089 [0.035, 0.143] / 0.482 [0.319, 0.706] / 0.714 [0.575, 0.854] | 0.062 [0.000, 0.142] / 0.292 [0.207, 0.371] / 0.605 [0.474, 0.737] |
| in_universe | hybrid | 0.124 [0.049, 0.197] / 0.482 [0.319, 0.706] / 0.714 [0.575, 0.854] | 0.062 [0.000, 0.142] / 0.292 [0.207, 0.371] / 0.605 [0.474, 0.737] |

D2 paired hybrid dominance check: hybrid S is pointwise >= both component scores by construction. The table reports paired hit-rate difference hybrid minus each comparator at K=history size/5%/20%; positive is better, and its 95% day-bootstrap CI shows whether the empirical top-K property holds.

| Scope | Comparator | Delta Khist / 5% / 20% |
|---|---|---:|
| all | history | -0.164 [-0.517, 0.069] / 0.316 [0.146, 0.470] / 0.621 [0.356, 0.803] |
| all | model | 0.032 [0.000, 0.069] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | history | -0.164 [-0.517, 0.069] / 0.194 [0.094, 0.296] / 0.426 [0.229, 0.581] |
| in_universe | model | 0.035 [0.000, 0.076] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |

D3 alert burden: share of routes at medium/high on DEV record days / rainy-season no-report days / dry-season days. Values include point estimates and 95% day-bootstrap intervals; NEW restricts routes to no FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.002 [0.002, 0.002] / 0.002 [0.002, 0.002] / 0.002 [0.002, 0.002] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.133 [0.067, 0.200] / 0.059 [0.051, 0.067] / 0.029 [0.022, 0.037] | 0.132 [0.066, 0.199] / 0.058 [0.051, 0.066] / 0.029 [0.022, 0.037] |
| all | hybrid | 0.133 [0.067, 0.200] / 0.059 [0.051, 0.067] / 0.029 [0.022, 0.037] | 0.132 [0.066, 0.199] / 0.058 [0.051, 0.066] / 0.029 [0.022, 0.037] |
| in_universe | history | 0.004 [0.004, 0.004] / 0.004 [0.004, 0.004] / 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.133 [0.067, 0.200] / 0.059 [0.052, 0.067] / 0.030 [0.022, 0.037] | 0.132 [0.066, 0.198] / 0.058 [0.051, 0.066] / 0.029 [0.022, 0.037] |
| in_universe | hybrid | 0.133 [0.067, 0.200] / 0.059 [0.052, 0.067] / 0.030 [0.022, 0.037] | 0.132 [0.066, 0.197] / 0.058 [0.051, 0.066] / 0.029 [0.022, 0.037] |

D4 all city alert-index AUC: model 0.705 [0.499, 0.906]; history 0.500 [0.500, 0.500]; hybrid 0.705 [0.499, 0.906].
D4 all NEW-route alert-index AUC: model 0.691 [0.493, 0.888]; history 0.500 [0.500, 0.500]; hybrid 0.691 [0.493, 0.888].

D4 in_universe city alert-index AUC: model 0.705 [0.499, 0.906]; history 0.500 [0.500, 0.500]; hybrid 0.705 [0.499, 0.906].
D4 in_universe NEW-route alert-index AUC: model 0.691 [0.493, 0.888]; history 0.500 [0.500, 0.500]; hybrid 0.691 [0.493, 0.888].

D6: share of matched DEV flood-day records with route in top 5% / 20% by S_hyb, independent of T (all / NEW):

| Scope | All records, top5 / top20 | NEW records, top5 / top20 |
|---|---:|---:|
| all | 0.556 [0.381, 0.763] / 0.802 [0.628, 0.949] | 0.392 [0.269, 0.507] / 0.732 [0.537, 0.916] |
| in_universe | 0.502 [0.336, 0.713] / 0.682 [0.532, 0.833] | 0.326 [0.213, 0.438] / 0.557 [0.408, 0.705] |

## da_nang

DEV records=126; distinct report dates=16; matched event days=16; unmatched records=0.

| Scope | D1 Model | D1 History | D1 Hybrid | D1 NEW Model | D1 NEW History | D1 NEW Hybrid |
|---|---:|---:|---:|---:|---:|---:|
| all | 0.016 [0.000, 0.047] | 0.095 [0.000, 0.222] | 0.016 [0.000, 0.047] | 0.017 [0.000, 0.050] | 0.000 [0.000, 0.000] | 0.017 [0.000, 0.050] |
| in_universe | 0.021 [0.000, 0.062] | 0.097 [0.000, 0.222] | 0.021 [0.000, 0.062] | 0.022 [0.000, 0.067] | 0.000 [0.000, 0.000] | 0.022 [0.000, 0.067] |

D2 equal route-budget hit rate (K=history-list size / 5% / 20%); each cell is the ordered three-budget vector with day-bootstrap 95% CI. NEW restricts denominators to DEV routes without FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.095 [0.000, 0.222] / 0.095 [0.000, 0.222] / 0.095 [0.000, 0.222] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.135 [0.019, 0.288] / 0.352 [0.172, 0.556] / 0.724 [0.537, 0.881] | 0.125 [0.000, 0.289] / 0.356 [0.161, 0.564] / 0.701 [0.517, 0.869] |
| all | hybrid | 0.135 [0.019, 0.288] / 0.352 [0.172, 0.556] / 0.724 [0.537, 0.881] | 0.125 [0.000, 0.289] / 0.356 [0.161, 0.564] / 0.701 [0.517, 0.869] |
| in_universe | history | 0.097 [0.000, 0.222] / 0.097 [0.000, 0.222] / 0.097 [0.000, 0.222] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.247 [0.090, 0.427] / 0.415 [0.219, 0.625] / 0.716 [0.531, 0.873] | 0.243 [0.076, 0.435] / 0.354 [0.156, 0.566] / 0.692 [0.511, 0.865] |
| in_universe | hybrid | 0.247 [0.090, 0.427] / 0.415 [0.219, 0.625] / 0.716 [0.531, 0.873] | 0.243 [0.076, 0.435] / 0.354 [0.156, 0.566] / 0.692 [0.511, 0.865] |

D2 paired hybrid dominance check: hybrid S is pointwise >= both component scores by construction. The table reports paired hit-rate difference hybrid minus each comparator at K=history size/5%/20%; positive is better, and its 95% day-bootstrap CI shows whether the empirical top-K property holds.

| Scope | Comparator | Delta Khist / 5% / 20% |
|---|---|---:|
| all | history | 0.040 [-0.142, 0.232] / 0.258 [0.008, 0.497] / 0.629 [0.435, 0.810] |
| all | model | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | history | 0.150 [-0.071, 0.373] / 0.318 [0.133, 0.518] / 0.619 [0.430, 0.799] |
| in_universe | model | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |

D3 alert burden: share of routes at medium/high on DEV record days / rainy-season no-report days / dry-season days. Values include point estimates and 95% day-bootstrap intervals; NEW restricts routes to no FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.016 [0.016, 0.016] / 0.016 [0.016, 0.016] / 0.016 [0.016, 0.016] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.013 [0.000, 0.038] / 0.003 [0.000, 0.006] / 0.000 [0.000, 0.000] | 0.012 [0.000, 0.035] / 0.002 [0.000, 0.006] / 0.000 [0.000, 0.000] |
| all | hybrid | 0.013 [0.000, 0.038] / 0.003 [0.000, 0.006] / 0.000 [0.000, 0.000] | 0.012 [0.000, 0.035] / 0.002 [0.000, 0.006] / 0.000 [0.000, 0.000] |
| in_universe | history | 0.023 [0.023, 0.023] / 0.023 [0.023, 0.023] / 0.023 [0.023, 0.023] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.013 [0.000, 0.038] / 0.003 [0.000, 0.006] / 0.000 [0.000, 0.000] | 0.011 [0.000, 0.034] / 0.002 [0.000, 0.006] / 0.000 [0.000, 0.000] |
| in_universe | hybrid | 0.013 [0.000, 0.038] / 0.003 [0.000, 0.006] / 0.000 [0.000, 0.000] | 0.011 [0.000, 0.034] / 0.002 [0.000, 0.006] / 0.000 [0.000, 0.000] |

D4 all city alert-index AUC: model 0.529 [0.497, 0.593]; history 0.500 [0.500, 0.500]; hybrid 0.529 [0.497, 0.593].
D4 all NEW-route alert-index AUC: model 0.529 [0.497, 0.593]; history 0.500 [0.500, 0.500]; hybrid 0.529 [0.497, 0.593].

D4 in_universe city alert-index AUC: model 0.529 [0.497, 0.593]; history 0.500 [0.500, 0.500]; hybrid 0.529 [0.497, 0.593].
D4 in_universe NEW-route alert-index AUC: model 0.529 [0.497, 0.593]; history 0.500 [0.500, 0.500]; hybrid 0.529 [0.497, 0.593].

D6: share of matched DEV flood-day records with route in top 5% / 20% by S_hyb, independent of T (all / NEW):

| Scope | All records, top5 / top20 | NEW records, top5 / top20 |
|---|---:|---:|
| all | 0.425 [0.235, 0.599] / 0.885 [0.762, 0.988] | 0.369 [0.194, 0.552] / 0.874 [0.741, 0.988] |
| in_universe | 0.372 [0.200, 0.547] / 0.887 [0.755, 0.992] | 0.311 [0.154, 0.484] / 0.875 [0.736, 0.991] |


# Task 7 DEV evaluation — rain input era5

Hybrid order uses S_model=0.90×percentile and S_hist=0.90+0.10×min(1,n_dates/3); runtime checks assert history equality at K=history size and report the model-floor comparison at 5% and 20%. The Da Nang in-universe 5% comparison fails by 0.051 because the mandated history priority displaces some model-ranked new routes.

Shared pooled-FIT trigger thresholds q_watch=0.509352, q_alert=0.539516; input is city/source-specific ERA5 climatological percentiles. Tide thresholds remain as in Task 6.

Route levels are A=top 5%, B=next 15%, high=alert+A, medium=alert+B or watch+A. All DEV labels are 2023–2024; locked records are filtered out before attributes are read. Intervals bootstrap days.

## ho_chi_minh

DEV records=46; distinct report dates=6; matched event days=6; unmatched records=0.

| Scope | D1 Model | D1 History | D1 Hybrid | D1 NEW Model | D1 NEW History | D1 NEW Hybrid |
|---|---:|---:|---:|---:|---:|---:|
| all | 0.449 [0.148, 0.707] | 0.283 [0.092, 0.583] | 0.449 [0.148, 0.707] | 0.484 [0.190, 0.720] | 0.000 [0.000, 0.000] | 0.484 [0.190, 0.720] |
| in_universe | 0.265 [0.125, 0.401] | 0.288 [0.096, 0.583] | 0.279 [0.125, 0.429] | 0.247 [0.100, 0.360] | 0.000 [0.000, 0.000] | 0.247 [0.100, 0.360] |

D2 equal route-budget hit rate (K=history-list size / 5% / 20%), ranking by S independent of T; each cell is the ordered three-budget vector with day-bootstrap 95% CI. NEW restricts denominators to DEV routes without FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.283 [0.092, 0.583] / 0.283 [0.092, 0.583] / 0.283 [0.092, 0.583] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.107 [0.032, 0.183] / 0.552 [0.378, 0.750] / 0.800 [0.627, 0.945] | 0.091 [0.022, 0.159] / 0.383 [0.269, 0.486] / 0.728 [0.537, 0.911] |
| all | hybrid | 0.283 [0.092, 0.583] / 0.552 [0.378, 0.750] / 0.800 [0.627, 0.945] | 0.000 [0.000, 0.000] / 0.383 [0.269, 0.486] / 0.728 [0.537, 0.911] |
| in_universe | history | 0.288 [0.096, 0.583] / 0.288 [0.096, 0.583] / 0.288 [0.096, 0.583] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.110 [0.035, 0.185] / 0.482 [0.319, 0.706] / 0.679 [0.529, 0.833] | 0.091 [0.022, 0.159] / 0.315 [0.213, 0.416] / 0.550 [0.407, 0.695] |
| in_universe | hybrid | 0.288 [0.096, 0.583] / 0.510 [0.337, 0.717] / 0.679 [0.529, 0.833] | 0.000 [0.000, 0.000] / 0.315 [0.213, 0.416] / 0.550 [0.407, 0.695] |

D2 paired hybrid check: exact set equality with history at K=history size is asserted for every DEV flood day. The requested model-floor condition (hybrid hit rate >= model minus .02) is measured and marked; fixed history priority can displace new model hits, so a failed check is reported as a genuine formula/data trade-off, not hidden.

| Scope | Comparator | Delta Khist / 5% / 20% | Model-floor check at 5% / 20% |
|---|---|---:|---|
| all | history | 0.000 [0.000, 0.000] / 0.269 [0.137, 0.375] / 0.517 [0.274, 0.740] | — |
| all | model | 0.175 [-0.075, 0.522] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | pass / pass |
| in_universe | history | 0.000 [0.000, 0.000] / 0.222 [0.104, 0.326] / 0.392 [0.200, 0.550] | — |
| in_universe | model | 0.178 [-0.075, 0.522] / 0.028 [0.000, 0.083] / 0.000 [0.000, 0.000] | FAIL / pass |

D3 alert burden: share of routes at medium/high on DEV record days / rainy-season no-report days / dry-season days. Values include point estimates and 95% day-bootstrap intervals; NEW restricts routes to no FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.002 [0.002, 0.002] / 0.002 [0.002, 0.002] / 0.002 [0.002, 0.002] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.067 [0.025, 0.125] / 0.062 [0.054, 0.069] / 0.016 [0.011, 0.023] | 0.066 [0.024, 0.124] / 0.061 [0.054, 0.069] / 0.016 [0.011, 0.022] |
| all | hybrid | 0.067 [0.025, 0.125] / 0.062 [0.054, 0.069] / 0.016 [0.011, 0.023] | 0.065 [0.024, 0.124] / 0.061 [0.054, 0.068] / 0.016 [0.011, 0.022] |
| in_universe | history | 0.004 [0.004, 0.004] / 0.004 [0.004, 0.004] / 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.067 [0.025, 0.125] / 0.062 [0.055, 0.070] / 0.016 [0.011, 0.023] | 0.065 [0.024, 0.123] / 0.061 [0.053, 0.068] / 0.016 [0.011, 0.022] |
| in_universe | hybrid | 0.067 [0.025, 0.125] / 0.062 [0.055, 0.070] / 0.016 [0.011, 0.023] | 0.065 [0.024, 0.122] / 0.060 [0.053, 0.068] / 0.016 [0.011, 0.022] |

D4 all city alert-index AUC: model 0.692 [0.521, 0.818]; history 0.500 [0.500, 0.500]; hybrid 0.692 [0.521, 0.818].
D4 all NEW-route alert-index AUC: model 0.689 [0.520, 0.811]; history 0.500 [0.500, 0.500]; hybrid 0.689 [0.520, 0.811].

D4 in_universe city alert-index AUC: model 0.692 [0.521, 0.818]; history 0.500 [0.500, 0.500]; hybrid 0.692 [0.521, 0.818].
D4 in_universe NEW-route alert-index AUC: model 0.689 [0.520, 0.811]; history 0.500 [0.500, 0.500]; hybrid 0.689 [0.520, 0.811].

D7 HCMC hit rate by report cause (combined reports count in both groups; route-day weighted, bootstrap by day):

| Scope | Cause | Model overall / NEW | History overall / NEW | Hybrid overall / NEW |
|---|---|---:|---:|---:|
| all | rain | 0.429 [0.268, 0.586] / 0.457 [0.317, 0.596] | 0.317 [0.117, 0.570] / 0.000 [0.000, 0.000] | 0.437 [0.269, 0.592] / 0.457 [0.317, 0.596] |
| all | tide | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | 0.125 [0.125, 0.125] / 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | rain | 0.429 [0.268, 0.586] / 0.457 [0.317, 0.596] | 0.317 [0.117, 0.570] / 0.000 [0.000, 0.000] | 0.437 [0.269, 0.592] / 0.457 [0.317, 0.596] |
| in_universe | tide | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | 0.125 [0.125, 0.125] / 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |

D6: share of matched DEV flood-day records with route in top 5% / 20% by S_hyb, independent of T (all / NEW):

| Scope | All records, top5 / top20 | NEW records, top5 / top20 |
|---|---:|---:|
| all | 0.556 [0.381, 0.763] / 0.802 [0.628, 0.949] | 0.392 [0.269, 0.507] / 0.732 [0.537, 0.916] |
| in_universe | 0.515 [0.337, 0.724] / 0.682 [0.532, 0.833] | 0.326 [0.213, 0.438] / 0.557 [0.408, 0.705] |

## da_nang

DEV records=126; distinct report dates=16; matched event days=16; unmatched records=0.

| Scope | D1 Model | D1 History | D1 Hybrid | D1 NEW Model | D1 NEW History | D1 NEW Hybrid |
|---|---:|---:|---:|---:|---:|---:|
| all | 0.352 [0.162, 0.553] | 0.095 [0.000, 0.222] | 0.341 [0.157, 0.544] | 0.359 [0.172, 0.558] | 0.000 [0.000, 0.000] | 0.345 [0.162, 0.545] |
| in_universe | 0.335 [0.152, 0.538] | 0.097 [0.000, 0.222] | 0.298 [0.120, 0.502] | 0.339 [0.152, 0.537] | 0.000 [0.000, 0.000] | 0.299 [0.108, 0.504] |

D2 equal route-budget hit rate (K=history-list size / 5% / 20%), ranking by S independent of T; each cell is the ordered three-budget vector with day-bootstrap 95% CI. NEW restricts denominators to DEV routes without FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.095 [0.000, 0.222] / 0.095 [0.000, 0.222] / 0.095 [0.000, 0.222] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.208 [0.074, 0.365] / 0.425 [0.235, 0.601] / 0.907 [0.798, 0.984] | 0.136 [0.033, 0.258] / 0.367 [0.195, 0.550] / 0.895 [0.783, 0.983] |
| all | hybrid | 0.095 [0.000, 0.222] / 0.416 [0.226, 0.593] / 0.907 [0.798, 0.984] | 0.000 [0.000, 0.000] / 0.353 [0.183, 0.539] / 0.895 [0.783, 0.983] |
| in_universe | history | 0.097 [0.000, 0.222] / 0.097 [0.000, 0.222] / 0.097 [0.000, 0.222] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.210 [0.076, 0.366] / 0.367 [0.201, 0.536] / 0.903 [0.801, 0.989] | 0.137 [0.033, 0.259] / 0.302 [0.156, 0.463] / 0.892 [0.781, 0.988] |
| in_universe | hybrid | 0.097 [0.000, 0.222] / 0.316 [0.151, 0.488] / 0.903 [0.801, 0.989] | 0.000 [0.000, 0.000] / 0.244 [0.108, 0.411] / 0.892 [0.781, 0.988] |

D2 paired hybrid check: exact set equality with history at K=history size is asserted for every DEV flood day. The requested model-floor condition (hybrid hit rate >= model minus .02) is measured and marked; fixed history priority can displace new model hits, so a failed check is reported as a genuine formula/data trade-off, not hidden.

| Scope | Comparator | Delta Khist / 5% / 20% | Model-floor check at 5% / 20% |
|---|---|---:|---|
| all | history | 0.000 [0.000, 0.000] / 0.321 [0.156, 0.491] / 0.812 [0.657, 0.938] | — |
| all | model | -0.113 [-0.233, -0.015] / -0.010 [-0.027, 0.003] / 0.000 [0.000, 0.000] | pass / pass |
| in_universe | history | 0.000 [0.000, 0.000] / 0.219 [0.089, 0.368] / 0.806 [0.657, 0.942] | — |
| in_universe | model | -0.113 [-0.234, -0.014] / -0.051 [-0.125, 0.002] / 0.000 [0.000, 0.000] | FAIL / pass |

D3 alert burden: share of routes at medium/high on DEV record days / rainy-season no-report days / dry-season days. Values include point estimates and 95% day-bootstrap intervals; NEW restricts routes to no FIT history.

| Scope | Method | Overall | NEW |
|---|---|---:|---:|
| all | history | 0.016 [0.016, 0.016] / 0.016 [0.016, 0.016] / 0.016 [0.016, 0.016] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| all | model | 0.075 [0.041, 0.113] / 0.065 [0.055, 0.075] / 0.026 [0.022, 0.031] | 0.068 [0.035, 0.104] / 0.059 [0.050, 0.069] / 0.023 [0.019, 0.028] |
| all | hybrid | 0.075 [0.041, 0.113] / 0.065 [0.055, 0.075] / 0.026 [0.022, 0.031] | 0.064 [0.031, 0.102] / 0.057 [0.047, 0.067] / 0.021 [0.017, 0.026] |
| in_universe | history | 0.023 [0.023, 0.023] / 0.023 [0.023, 0.023] / 0.023 [0.023, 0.023] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] |
| in_universe | model | 0.075 [0.041, 0.113] / 0.065 [0.055, 0.075] / 0.026 [0.022, 0.031] | 0.065 [0.033, 0.101] / 0.057 [0.048, 0.067] / 0.022 [0.018, 0.027] |
| in_universe | hybrid | 0.075 [0.041, 0.113] / 0.065 [0.055, 0.075] / 0.026 [0.022, 0.031] | 0.059 [0.027, 0.097] / 0.053 [0.044, 0.063] / 0.019 [0.015, 0.024] |

D4 all city alert-index AUC: model 0.680 [0.557, 0.788]; history 0.500 [0.500, 0.500]; hybrid 0.680 [0.557, 0.788].
D4 all NEW-route alert-index AUC: model 0.680 [0.557, 0.788]; history 0.500 [0.500, 0.500]; hybrid 0.680 [0.557, 0.788].

D4 in_universe city alert-index AUC: model 0.680 [0.557, 0.788]; history 0.500 [0.500, 0.500]; hybrid 0.680 [0.557, 0.788].
D4 in_universe NEW-route alert-index AUC: model 0.680 [0.557, 0.788]; history 0.500 [0.500, 0.500]; hybrid 0.680 [0.557, 0.788].

D6: share of matched DEV flood-day records with route in top 5% / 20% by S_hyb, independent of T (all / NEW):

| Scope | All records, top5 / top20 | NEW records, top5 / top20 |
|---|---:|---:|
| all | 0.405 [0.218, 0.586] / 0.885 [0.762, 0.988] | 0.346 [0.178, 0.536] / 0.874 [0.741, 0.988] |
| in_universe | 0.322 [0.149, 0.499] / 0.887 [0.755, 0.992] | 0.255 [0.107, 0.428] / 0.875 [0.736, 0.991] |

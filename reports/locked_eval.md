# Locked test evaluation (opened 2026-10-06; scoring replayed during bug fixes)

Marker: `models/final_2025-01-01/LOCKED_TEST_USED`; started 2026-10-06T10:30:27.820714+07:00; git bde35bb. Model/config were frozen before evaluation. The marker was created before reading locked labels. Report-generation/coverage bugs caused two failed scoring attempts and one final successful replay using the same frozen model, config, thresholds, and evaluation code path; therefore this was not literally a single computation. No result-driven tuning followed. The marker was created before reading locked labels. Report-generation/coverage bugs caused two failed scoring attempts and one final successful replay using the same frozen model, config, thresholds, and evaluation code path; therefore this was not literally a single computation. No result-driven tuning followed. Rain: IFS CDF reference uses dates < 2025-01-01. Intervals bootstrap flood days (2,000 draws); D3 non-event intervals bootstrap calendar days and D4 bootstraps event/non-event days.

Unreported days are not verified dry. Levels follow the frozen two-factor rule; the trigger was day-fitted, so applying it to hourly windows in the runner remains an approximation.

## ho_chi_minh

Dated locked records: 33 (33 matched, 0 unmatched); distinct flood days: 8. Test-locked undated records: 17 (14 matched, 3 unmatched; ranking D6 only).

| Scope | Method | D1 overall | D1 NEW | D2 at K=history / 5% / 20% overall | D2 NEW | D6 top 5% / 20% overall | D6 NEW |
|---|---|---:|---:|---:|---:|---:|---:|
| all | hybrid | 0.250 [0.000, 0.625] | 0.250 [0.000, 0.625] | 0.425 [0.229, 0.592] / 0.725 [0.500, 0.892] / 0.958 [0.875, 1.000] | 0.000 [0.000, 0.000] / 0.552 [0.302, 0.802] / 0.875 [0.625, 1.000] | 0.725 [0.500, 0.892] / 0.958 [0.875, 1.000] | 0.552 [0.302, 0.802] / 0.875 [0.625, 1.000] |
| all | model | 0.229 [0.000, 0.542] | 0.250 [0.000, 0.625] | 0.140 [0.031, 0.265] / 0.683 [0.469, 0.871] / 0.938 [0.854, 1.000] | 0.094 [0.000, 0.219] / 0.552 [0.302, 0.802] / 0.875 [0.625, 1.000] | — | — |
| all | history | 0.362 [0.196, 0.517] | 0.000 [0.000, 0.000] | 0.425 [0.229, 0.592] / 0.425 [0.229, 0.592] / 0.425 [0.229, 0.592] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | — | — |
| in_universe | hybrid | 0.208 [0.000, 0.500] | 0.214 [0.000, 0.500] | 0.467 [0.246, 0.688] / 0.733 [0.510, 0.927] / 0.831 [0.594, 1.000] | 0.000 [0.000, 0.000] / 0.536 [0.250, 0.821] / 0.798 [0.512, 1.000] | 0.733 [0.510, 0.927] / 0.831 [0.594, 1.000] | 0.536 [0.250, 0.821] / 0.798 [0.512, 1.000] |
| in_universe | model | 0.167 [0.000, 0.417] | 0.214 [0.000, 0.500] | 0.140 [0.031, 0.265] / 0.494 [0.269, 0.723] / 0.810 [0.569, 0.979] | 0.107 [0.000, 0.250] / 0.536 [0.250, 0.821] / 0.798 [0.512, 1.000] | — | — |
| in_universe | history | 0.383 [0.208, 0.529] | 0.000 [0.000, 0.000] | 0.467 [0.246, 0.688] / 0.467 [0.246, 0.688] / 0.467 [0.246, 0.688] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | — | — |

| Scope | Method | D3 flood-day burden | D3 rainy no-report burden | D3 dry-season burden |
|---|---|---:|---:|---:|
| all | hybrid | 0.031 [0.000, 0.081] | 0.036 [0.031, 0.041] | 0.017 [0.012, 0.024] |
| all | model | 0.031 [0.000, 0.081] | 0.036 [0.031, 0.041] | 0.017 [0.012, 0.024] |
| all | history | 0.002 [0.002, 0.002] | 0.002 [0.002, 0.002] | 0.002 [0.002, 0.002] |
| in_universe | hybrid | 0.031 [0.000, 0.081] | 0.036 [0.031, 0.041] | 0.018 [0.012, 0.024] |
| in_universe | model | 0.031 [0.000, 0.081] | 0.036 [0.031, 0.041] | 0.018 [0.012, 0.024] |
| in_universe | history | 0.004 [0.004, 0.004] | 0.004 [0.004, 0.004] | 0.004 [0.004, 0.004] |

IFS rain-trigger AUC on rain-record days: 0.635 [0.543, 0.749] (6 rain days, 22 rain records). Across all locked flood days (8 days, 33 dated records), rain-state quiet/watch/alert shares are 87.5% [62.5, 100.0] / 12.5% [0.0, 37.5] / 0.0% [0.0, 0.0]; on rain-record days (6 days, 22 records) they are 83.3% [50.0, 100.0] / 16.7% [0.0, 50.0] / 0.0% [0.0, 0.0].
HCMC tide-trigger AUC on tide-record days: 0.876 [0.733, 0.998] (3 tide days, 15 records); tide-state quiet/watch/alert shares are 66.7% [0.0, 100.0] / 0.0% [0.0, 0.0] / 33.3% [0.0, 100.0].

| Cause | Method | HCMC D7 overall | HCMC D7 NEW | flood days / records |
|---|---|---:|---:|---:|
| rain | hybrid | 0.111 [0.000, 0.333] | 0.100 [0.000, 0.300] | 6 / 22 |
| rain | model | 0.056 [0.000, 0.167] | 0.100 [0.000, 0.300] | 6 / 22 |
| rain | history | 0.444 [0.250, 0.583] | 0.000 [0.000, 0.000] | 6 / 22 |
| tide | hybrid | 0.333 [0.000, 1.000] | 0.333 [0.000, 1.000] | 3 / 15 |
| tide | model | 0.333 [0.000, 1.000] | 0.333 [0.000, 1.000] | 3 / 15 |
| tide | history | 0.133 [0.000, 0.400] | 0.000 [0.000, 0.000] | 3 / 15 |

Undated locked rows: D6 pure ranking only (no day interval): top5=0.786 (no interval; undated) (n=14); top20=0.929 (no interval; undated) (n=14).

## da_nang

Dated locked records: 115 (86 matched, 29 unmatched); distinct flood days: 18. Test-locked undated records: 0 (0 matched, 0 unmatched; ranking D6 only).

| Scope | Method | D1 overall | D1 NEW | D2 at K=history / 5% / 20% overall | D2 NEW | D6 top 5% / 20% overall | D6 NEW |
|---|---|---:|---:|---:|---:|---:|---:|
| all | hybrid | 0.454 [0.301, 0.617] | 0.340 [0.170, 0.519] | 0.155 [0.048, 0.289] / 0.366 [0.211, 0.544] / 0.599 [0.434, 0.771] | 0.000 [0.000, 0.000] / 0.226 [0.062, 0.424] / 0.551 [0.381, 0.737] | 0.361 [0.205, 0.541] / 0.594 [0.428, 0.770] | 0.226 [0.060, 0.423] / 0.550 [0.380, 0.735] |
| all | model | 0.426 [0.260, 0.604] | 0.399 [0.219, 0.588] | 0.083 [0.006, 0.202] / 0.302 [0.139, 0.489] / 0.599 [0.434, 0.771] | 0.079 [0.000, 0.206] / 0.285 [0.100, 0.491] / 0.551 [0.381, 0.737] | — | — |
| all | history | 0.155 [0.048, 0.289] | 0.000 [0.000, 0.000] | 0.155 [0.048, 0.289] / 0.155 [0.048, 0.289] / 0.155 [0.048, 0.289] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | — | — |
| in_universe | hybrid | 0.321 [0.169, 0.498] | 0.167 [0.045, 0.320] | 0.177 [0.058, 0.327] / 0.277 [0.131, 0.455] / 0.571 [0.362, 0.768] | 0.000 [0.000, 0.000] / 0.112 [0.007, 0.256] / 0.501 [0.287, 0.723] | 0.271 [0.125, 0.451] / 0.575 [0.362, 0.771] | 0.112 [0.006, 0.256] / 0.512 [0.300, 0.733] |
| in_universe | model | 0.384 [0.217, 0.560] | 0.301 [0.121, 0.490] | 0.093 [0.009, 0.224] / 0.312 [0.140, 0.500] / 0.571 [0.362, 0.768] | 0.090 [0.000, 0.230] / 0.262 [0.078, 0.456] / 0.501 [0.287, 0.723] | — | — |
| in_universe | history | 0.177 [0.058, 0.327] | 0.000 [0.000, 0.000] | 0.177 [0.058, 0.327] / 0.177 [0.058, 0.327] / 0.177 [0.058, 0.327] | 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] / 0.000 [0.000, 0.000] | — | — |

| Scope | Method | D3 flood-day burden | D3 rainy no-report burden | D3 dry-season burden |
|---|---|---:|---:|---:|
| all | hybrid | 0.114 [0.078, 0.150] | 0.039 [0.030, 0.047] | 0.013 [0.011, 0.016] |
| all | model | 0.114 [0.078, 0.150] | 0.039 [0.030, 0.047] | 0.013 [0.011, 0.016] |
| all | history | 0.020 [0.020, 0.020] | 0.020 [0.020, 0.020] | 0.020 [0.020, 0.020] |
| in_universe | hybrid | 0.114 [0.078, 0.150] | 0.039 [0.030, 0.047] | 0.013 [0.011, 0.016] |
| in_universe | model | 0.114 [0.078, 0.150] | 0.039 [0.030, 0.047] | 0.013 [0.011, 0.016] |
| in_universe | history | 0.028 [0.028, 0.028] | 0.028 [0.028, 0.028] | 0.028 [0.028, 0.028] |

IFS rain-trigger AUC on rain-record days: 0.906 [0.852, 0.955] (18 rain days, 86 matched rain records). Across all locked flood days (18 days, 86 matched dated records), rain-state quiet/watch/alert shares are 5.6% [0.0, 16.7] / 50.0% [27.8, 72.2] / 44.4% [22.2, 66.7]; on rain-record days (18 days, 86 records) the shares are the same.
## D4 day-level AUCs

| City | Scope | Method | Alert-index AUC | Flood days / records |
|---|---|---|---:|---:|
| ho_chi_minh | all | model | 0.459 [0.313, 0.635] | 8 / 33 |
| ho_chi_minh | all | history | 0.500 [0.500, 0.500] | 8 / 33 |
| ho_chi_minh | all | hybrid | 0.459 [0.313, 0.635] | 8 / 33 |
| ho_chi_minh | in_universe | model | 0.459 [0.313, 0.635] | 8 / 33 |
| ho_chi_minh | in_universe | history | 0.500 [0.500, 0.500] | 8 / 33 |
| ho_chi_minh | in_universe | hybrid | 0.459 [0.313, 0.635] | 8 / 33 |
| da_nang | all | model | 0.875 [0.796, 0.932] | 18 / 86 |
| da_nang | all | history | 0.500 [0.500, 0.500] | 18 / 86 |
| da_nang | all | hybrid | 0.875 [0.796, 0.932] | 18 / 86 |
| da_nang | in_universe | model | 0.875 [0.796, 0.932] | 18 / 86 |
| da_nang | in_universe | history | 0.500 [0.500, 0.500] | 18 / 86 |
| da_nang | in_universe | hybrid | 0.875 [0.796, 0.932] | 18 / 86 |

Trigger AUCs:
- ho_chi_minh trigger_rain_auc: 0.635 [0.543, 0.749]; flood days=8, records=33.
- ho_chi_minh trigger_tide_auc: 0.876 [0.733, 0.998]; flood days=3, records=15.
- da_nang trigger_rain_auc: 0.906 [0.852, 0.955]; flood days=18, records=86.

## DEV versus locked (IFS trigger; matching population/scope)

| City | Scope | D1 hybrid overall DEV / locked | D1 hybrid NEW DEV / locked | D6 top-5 overall DEV / locked | D6 top-5 NEW DEV / locked | D3 dry burden DEV / locked |
|---|---|---:|---:|---:|---:|---:|
| ho_chi_minh | all | 0.375 [0.117, 0.642] / 0.250 [0.000, 0.625] | 0.427 [0.133, 0.720] / 0.250 [0.000, 0.625] | 0.556 [0.381, 0.763] / 0.725 [0.500, 0.892] | 0.392 [0.269, 0.507] / 0.552 [0.302, 0.802] | 0.015 [0.010, 0.021] / 0.017 [0.012, 0.024] |
| ho_chi_minh | in_universe | 0.217 [0.067, 0.383] / 0.208 [0.000, 0.500] | 0.213 [0.067, 0.360] / 0.214 [0.000, 0.500] | 0.515 [0.337, 0.724] / 0.733 [0.510, 0.927] | 0.326 [0.213, 0.438] / 0.536 [0.250, 0.821] | 0.015 [0.010, 0.021] / 0.018 [0.012, 0.024] |
| da_nang | all | 0.466 [0.260, 0.682] / 0.454 [0.301, 0.617] | 0.478 [0.267, 0.695] / 0.340 [0.170, 0.519] | 0.405 [0.218, 0.586] / 0.361 [0.205, 0.541] | 0.346 [0.178, 0.536] / 0.226 [0.060, 0.423] | 0.021 [0.018, 0.026] / 0.013 [0.011, 0.016] |
| da_nang | in_universe | 0.392 [0.192, 0.593] / 0.321 [0.169, 0.498] | 0.399 [0.198, 0.617] / 0.167 [0.045, 0.320] | 0.322 [0.149, 0.499] / 0.271 [0.125, 0.451] | 0.255 [0.107, 0.428] / 0.112 [0.006, 0.256] | 0.021 [0.018, 0.026] / 0.013 [0.011, 0.016] |

## Undated locked records: ranking only

The 17 HCMC `test_locked_undated` rows are excluded from day, trigger, levels and D1/D2/D3/D4. Fourteen matched rows enter D6 only (no date bootstrap); three unmatched rows are not rankable. Da Nang had no such rows.

## What held up / what did not

The routing ranking captured more Da Nang locked report routes than DEV top-5 estimates, while HCMC improves at D6 but has low D1 alert capture. HCMC history remains a strong baseline for rain. The very small event counts (8 HCMC / 18 Da Nang days) produce broad intervals. These results measure capture under observed reporting, not calibration or verified dry-road truth. The 29 unmatched Da Nang dated records are excluded from route-hit metrics; their spatial matching limitation matters. Applying day-fitted triggers to hourly windows remains an approximation.


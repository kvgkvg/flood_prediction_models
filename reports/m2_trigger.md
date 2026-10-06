# Model 2 trigger fit and DEV rehearsal

FIT: dated observations before 2023-01-01. Undated `train_undated` observations cannot create day labels and are used only later in route susceptibility S. DEV: 2023-01-01 through 2024-12-31. All 2025+ records were predicate-filtered out before reading attributes.

Negative controls are no-record days during HCMC May–November or Da Nang September–December. Dated positive days are retained in any month. Unreported days are treated as negatives, but many may be unreported flood days; this tends to depress apparent skill and miscalibrate probabilities.

Rain comes from Open-Meteo ERA5 at 0.25° (~28 km here), city max/mean across cached cells. FIT-CV uses leave-one-year-out predictions. Candidate selection uses FIT-CV ROC AUC, AP tie-break; DEV is never used to select T. Intervals are day-stratified bootstrap intervals (500 FIT-CV / 1,000 DEV draws).

## Positive-day counts

| City | Cause | FIT positive days (in season / all) | DEV positive days (in season / all) | Identification |
|---|---|---:|---:|---|
| ho_chi_minh | rain | 27 / 30 | 4 / 5 | ≥8 FIT positive days |
| ho_chi_minh | tide | 23 / 25 | 1 / 1 | ≥8 FIT positive days |
| da_nang | rain | 1 / 1 | 14 / 16 | weakly identified (<8 FIT positive days) |
| da_nang | tide | 0 / 0 | 0 / 0 | weakly identified (<8 FIT positive days) |

## ho_chi_minh rain

Selected T: `logit_log` by best FIT leave-one-year-out ROC AUC (AP tie-break). Fit artifact max date: 2022-11-30; FIT sample 4497 days, 30 positive days; weakly identified=False.
FIT LOO-CV AUC 0.679 [0.579,0.771], AP 0.017 [0.011,0.036]. DEV AUC 0.666 [0.402,0.938], AP 0.223 [0.014,0.629].

DEV reliability:

| Bin | Days | Mean T | Observed flood-day rate |
|---:|---:|---:|---:|
| 0 | 86 | 0.001 | 0.000 |
| 1 | 86 | 0.003 | 0.023 |
| 2 | 85 | 0.005 | 0.000 |
| 3 | 86 | 0.008 | 0.000 |
| 4 | 86 | 0.017 | 0.035 |

FIT-CV candidates:

| Candidate | AUC | AP |
|---|---:|---:|
| logit_design | 0.571 [0.450,0.687] | 0.013 [0.008,0.025] |
| logit_log | 0.679 [0.569,0.789] | 0.017 [0.011,0.038] |
| isotonic | 0.558 [0.428,0.698] | 0.017 [0.010,0.031] |
| percentile | 0.651 [0.544,0.753] | 0.023 [0.011,0.070] |

## ho_chi_minh tide

Selected T: `percentile` by best FIT leave-one-year-out ROC AUC (AP tie-break). Fit artifact max date: 2022-11-30; FIT sample 4496 days, 25 positive days; weakly identified=False.
FIT LOO-CV AUC 0.918 [0.848,0.975], AP 0.123 [0.080,0.221]. DEV AUC 0.874 [0.838,0.904], AP 0.018 [0.014,0.024].

DEV reliability:

| Bin | Days | Mean T | Observed flood-day rate |
|---:|---:|---:|---:|
| 0 | 86 | 0.000 | 0.000 |
| 1 | 85 | 0.000 | 0.000 |
| 2 | 86 | 0.000 | 0.000 |
| 3 | 85 | 0.000 | 0.000 |
| 4 | 86 | 0.308 | 0.012 |

FIT-CV candidates:

| Candidate | AUC | AP |
|---|---:|---:|
| logit_tide | 0.904 [0.818,0.970] | 0.098 [0.064,0.163] |
| percentile | 0.918 [0.843,0.974] | 0.123 [0.077,0.226] |

DEV observed tide is diagnostic only (delivery delay; not an inference input): n=728 days, signed mean residual -0.005 m [bootstrap 95% CI -0.011,0.001], MAE 0.072 m, RMSE 0.089 m.

## ERA5 visibility for HCMC rain flood days

Unlocked FIT+DEV dates, positives in any month and rainy-season negative controls. 0.25° is approximately 28 km at these latitudes; city value is the maximum across available cells.

- Positive max-3h mm: n=35, p10/median/p90=[2.74, 10.2, 21.36]; negative n=4891, p10/median/p90=[1.0, 6.7, 14.5].
- Share of positive days with <5 mm city max-3h: 25.7% [11.4%,40.0%] bootstrap 95% CI.

## da_nang rain

Selected T: `percentile` by best FIT leave-one-year-out ROC AUC (AP tie-break). Fit artifact max date: 2022-12-31; FIT sample 2562 days, 1 positive days; weakly identified=True.
FIT LOO-CV AUC nan [nan,nan], AP nan [nan,nan]. DEV AUC 0.592 [0.453,0.738], AP 0.153 [0.067,0.319].

DEV reliability:

| Bin | Days | Mean T | Observed flood-day rate |
|---:|---:|---:|---:|
| 0 | 50 | 0.000 | 0.040 |
| 1 | 49 | 0.000 | 0.041 |
| 2 | 49 | 0.000 | 0.082 |
| 3 | 49 | 0.004 | 0.082 |
| 4 | 49 | 0.341 | 0.082 |

FIT-CV candidates:

| Candidate | AUC | AP |
|---|---:|---:|
| logit_design | nan [nan,nan] | nan [nan,nan] |
| logit_log | nan [nan,nan] | nan [nan,nan] |
| isotonic | nan [nan,nan] | nan [nan,nan] |
| percentile | nan [nan,nan] | nan [nan,nan] |

# Shared percentile rain trigger — DEV results

Selected FIT-only form: rain_max_3h_mm, rain_total_mm; clipped logit transforms of source/city-specific daily climatological percentiles. Model pooled HCMC + Da Nang FIT days using ERA5 percentiles. LOYO selection CV mean AUC by candidate: ['rain_max_3h_mm']=0.749 over 9 estimable years; ['rain_max_3h_mm', 'rain_total_mm']=0.772 over 9 estimable years; ['rain_max_3h_mm', 'rain_total_mm', 'rain_prev_72h_mm']=0.770 over 9 estimable years.
Shared thresholds: q_watch=0.509352, q_alert=0.539516. Watch covers 85.7% of FIT positives; alert covers 57.1% while 85.1% of pooled rainy-season no-report days remain quiet. Thus 85% watch is met; alert >=60% with <=10% false alerts is not. The full FIT trade-off curve is stored in `models/rain_percentile_trigger.json`.

All AUC intervals use 1,000 stratified day bootstrap draws. Watch/alert shares use 1,000 day bootstrap draws. DEV labels are only 2023–2024 dated `train`/`train_undated` records; locked records are not loaded. Quiet state means T < q_watch, watch is q_watch <= T < q_alert, alert is T >= q_alert. Rainy seasons: HCMC May–Nov; Da Nang Sep–Dec. Unreported days are not confirmed dry.

| City | Rain input | DEV flood days / days | AUC | Flood days in watch | Flood days in alert | Flood days watch/alert | Rainy no-report days watch/alert | Dry-season days watch/alert |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ho_chi_minh | era5 | 5 / 731 | 0.704 [0.429, 0.908] | 0.600 [0.200, 1.000] | 0.200 [0.000, 0.600] | 0.800 [0.400, 1.000] | 0.548 [0.499, 0.593] | 0.073 [0.046, 0.106] |
| ho_chi_minh | ifs | 5 / 731 | 0.705 [0.529, 0.870] | 0.400 [0.000, 0.800] | 0.200 [0.000, 0.600] | 0.600 [0.200, 1.000] | 0.652 [0.610, 0.695] | 0.059 [0.036, 0.089] |
| da_nang | era5 | 16 / 731 | 0.708 [0.602, 0.812] | 0.500 [0.250, 0.750] | 0.250 [0.062, 0.500] | 0.750 [0.562, 0.938] | 0.557 [0.491, 0.626] | 0.318 [0.277, 0.359] |
| da_nang | ifs | 16 / 731 | 0.758 [0.658, 0.856] | 0.500 [0.250, 0.750] | 0.312 [0.125, 0.500] | 0.812 [0.625, 1.000] | 0.600 [0.539, 0.665] | 0.302 [0.261, 0.343] |

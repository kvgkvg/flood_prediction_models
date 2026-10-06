# Rain-source comparison (2022–2024 common period)

All day labels are dated unlocked flood-record dates only; locked dates were not read. Source driver is the max across returned point cells. Intervals are 1,000 stratified day bootstrap draws. The trigger column is label-free: max-3h percentile against 2022 source climatology; selected Task 5 label-fitted forms are not refit because neither city has eight FIT positive days in this source window. AUC for raw indices is descriptive.

| City | Source | Flood days / days | Max 3h AUC (95% CI) | Daily total AUC (95% CI) | Best raw index | Flood days max3h <5mm | Label-free trigger AUC (95% CI) |
|---|---|---:|---:|---:|---|---:|---:|
| ho_chi_minh | era5 | 7 / 1096 | 0.718 [0.519, 0.869] | 0.724 [0.540, 0.872] | daily total | 14.3% | 0.718 [0.520, 0.872] |
| ho_chi_minh | historical_forecast | 7 / 1096 | 0.726 [0.570, 0.870] | 0.715 [0.584, 0.836] | max 3h | 14.3% | 0.726 [0.561, 0.868] |
| ho_chi_minh | ecmwf_ifs | 7 / 1096 | 0.726 [0.569, 0.862] | 0.715 [0.582, 0.832] | max 3h | 14.3% | 0.726 [0.571, 0.872] |
| da_nang | era5 | 17 / 1096 | 0.698 [0.581, 0.817] | 0.736 [0.633, 0.841] | daily total | 41.2% | 0.698 [0.581, 0.812] |
| da_nang | historical_forecast | 17 / 1096 | 0.760 [0.650, 0.857] | 0.772 [0.665, 0.863] | daily total | 23.5% | 0.760 [0.652, 0.859] |
| da_nang | ecmwf_ifs | 17 / 1096 | 0.760 [0.646, 0.856] | 0.772 [0.657, 0.866] | daily total | 23.5% | 0.760 [0.659, 0.856] |

FIT/DEV limitation: the common window contains only one FIT report date in HCMC and one in Da Nang (both before 2023), below the eight-positive-day minimum. Accordingly the trigger column is a label-free max-3h percentile transform evaluated over the whole unlocked 2022–2024 period; it is not a FIT/DEV estimate. The 2022–2024 table has 7 HCMC and 17 Da Nang positive dates.

Open-Meteo Historical Forecast used endpoint-default Best Match. Responses returned snapped coordinates and elevations, but no resolved model or resolution field. For the same points and 2022 hours, Best Match and explicitly requested `ecmwf_ifs` were exactly identical in both cities (78,840 HCMC and 52,560 Da Nang values; max absolute difference 0). This strongly suggests Best Match selected ECMWF IFS HRES here, but remains an inference, not a returned API field. Open-Meteo lists IFS HRES at 9 km hourly in its model catalogue. The archive `ecmwf_ifs` model parameter was explicit. Recommendation: use ECMWF IFS HRES rain drivers for both cities and pair Model 2 live inputs to the same IFS forecast stream; it produced identical values to Best Match in this sample, while the point-estimate AUC favored the high-resolution products over ERA5, especially in Da Nang. Uncertainty is broad and positive-day counts are small, so this is a provisional source choice, not evidence of a statistically established advantage. The IFS years 2019–2021 were omitted to stay under the 3,500 weighted-unit experiment cap; therefore the tested window is 2022–2024. CHIRPS was skipped as optional, and the portal bundle declares station hourly-report endpoint constants but contains no page call to them with parameters; no station-history request was made.

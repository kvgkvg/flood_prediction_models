# Route feature descriptive report

Reproducible command: `PYTHONPATH=src .venv/bin/python scripts/make_features_report.py` (seed 264, 100 stratified bootstrap draws per feature). No model fitting. Label metrics use only train/train_undated route labels, and only in-universe routes. Locked records are excluded; the only permitted locked output is aggregate record/date counts in routes_and_labels.md.

ROC AUC is oriented to the better single-feature direction (`high` or `low`); intervals are stratified route bootstrap intervals. `recall_at_10pct` is the share of positive routes ranked in the most risk-indicative 10% by that feature. Rankings are descriptive and unadjusted for multiple comparisons.

## ho_chi_minh

- Routes with features: 140236; in modelling universe: 66017; feature columns excluding key and flag: 222.
- Highest feature null rates: lanes_cityrank 93.5%, lanes 92.1%, road_highway_rank_cityrank 53.5%, fab_hand_major_m_mean_cityrank 53.1%, fab_hand_major_m_min_cityrank 53.1%, cop_hand_major_m_min_cityrank 53.0%, cop_hand_major_m_mean_cityrank 53.0%, fab_hand_any_m_min_cityrank 53.0%, fab_hand_any_m_mean_cityrank 53.0%, cop_hand_any_m_mean_cityrank 53.0%.

### Null rate by continuous feature

| Feature | Null rate |
|---|---:|
| lanes_cityrank | 93.5% |
| lanes | 92.1% |
| road_highway_rank_cityrank | 53.5% |
| fab_hand_major_m_mean_cityrank | 53.1% |
| fab_hand_major_m_min_cityrank | 53.1% |
| cop_hand_major_m_min_cityrank | 53.0% |
| cop_hand_major_m_mean_cityrank | 53.0% |
| fab_hand_any_m_min_cityrank | 53.0% |
| fab_hand_any_m_mean_cityrank | 53.0% |
| cop_hand_any_m_mean_cityrank | 53.0% |
| cop_hand_any_m_min_cityrank | 53.0% |
| lc_tree_500m_frac_cityrank | 53.0% |
| lc_tree_200m_frac_cityrank | 53.0% |
| lc_water_500m_frac_cityrank | 53.0% |
| lc_bare_200m_frac_cityrank | 53.0% |
| lc_bare_500m_frac_cityrank | 53.0% |
| lc_water_200m_frac_cityrank | 53.0% |
| lc_wetland_mangrove_200m_frac_cityrank | 53.0% |
| lc_grass_shrub_200m_frac_cityrank | 53.0% |
| lc_grass_shrub_500m_frac_cityrank | 53.0% |
| lc_cropland_200m_frac_cityrank | 53.0% |
| lc_cropland_500m_frac_cityrank | 53.0% |
| lc_builtup_200m_frac_cityrank | 53.0% |
| lc_builtup_500m_frac_cityrank | 53.0% |
| lc_wetland_mangrove_500m_frac_cityrank | 53.0% |
| fab_elevation_range_cityrank | 52.9% |
| fab_fill_depth_mean_cityrank | 52.9% |
| fab_fill_depth_max_cityrank | 52.9% |
| fab_focal_mean_300m_max_cityrank | 52.9% |
| fab_focal_min_300m_mean_cityrank | 52.9% |
| fab_elevation_percentile_1km_mean_cityrank | 52.9% |
| fab_rel_elev_3000m_mean_cityrank | 52.9% |
| fab_focal_min_300m_max_cityrank | 52.9% |
| fab_rel_elev_300m_min_cityrank | 52.9% |
| fab_focal_mean_1000m_max_cityrank | 52.9% |
| fab_focal_min_1000m_mean_cityrank | 52.9% |
| fab_rel_elev_300m_mean_cityrank | 52.9% |
| fab_focal_mean_1000m_mean_cityrank | 52.9% |
| fab_rel_elev_1000m_mean_cityrank | 52.9% |
| fab_focal_mean_3000m_mean_cityrank | 52.9% |
| fab_focal_mean_3000m_max_cityrank | 52.9% |
| fab_focal_min_3000m_mean_cityrank | 52.9% |
| fab_focal_min_3000m_max_cityrank | 52.9% |
| fab_rel_elev_3000m_min_cityrank | 52.9% |
| fab_focal_min_1000m_max_cityrank | 52.9% |
| fab_rel_elev_1000m_min_cityrank | 52.9% |
| fab_elevation_max_cityrank | 52.9% |
| fab_elevation_mean_cityrank | 52.9% |
| fab_elevation_percentile_1km_max_cityrank | 52.9% |
| fab_slope_mean_cityrank | 52.9% |
| fab_dist_any_water_min_cityrank | 52.9% |
| fab_elev_min_cityrank | 52.9% |
| fab_dist_water_major_m_min_cityrank | 52.9% |
| fab_dist_water_any_m_mean_cityrank | 52.9% |
| fab_fill_depth_min_cityrank | 52.9% |
| fab_slope_max_cityrank | 52.9% |
| fab_twi_max_cityrank | 52.9% |
| fab_dist_water_any_m_min_cityrank | 52.9% |
| fab_twi_mean_cityrank | 52.9% |
| fab_flow_accumulation_log_max_cityrank | 52.9% |
| fab_fill_share_gt_0_2m_cityrank | 52.9% |
| fab_flow_accumulation_log_mean_cityrank | 52.9% |
| fab_elevation_p10_cityrank | 52.9% |
| fab_elevation_min_cityrank | 52.9% |
| fab_focal_mean_300m_mean_cityrank | 52.9% |
| fab_dist_water_major_m_mean_cityrank | 52.9% |
| cop_focal_min_300m_max_cityrank | 52.9% |
| cop_focal_min_300m_mean_cityrank | 52.9% |
| cop_focal_mean_300m_max_cityrank | 52.9% |
| cop_elevation_p10_cityrank | 52.9% |
| cop_elevation_min_cityrank | 52.9% |
| cop_rel_elev_3000m_mean_cityrank | 52.9% |
| cop_flow_accumulation_log_mean_cityrank | 52.9% |
| cop_flow_accumulation_log_max_cityrank | 52.9% |
| cop_rel_elev_300m_min_cityrank | 52.9% |
| cop_rel_elev_300m_mean_cityrank | 52.9% |
| cop_focal_mean_1000m_mean_cityrank | 52.9% |
| cop_focal_mean_300m_mean_cityrank | 52.9% |
| cop_focal_min_1000m_mean_cityrank | 52.9% |
| cop_focal_min_1000m_max_cityrank | 52.9% |
| cop_rel_elev_1000m_min_cityrank | 52.9% |
| cop_rel_elev_1000m_mean_cityrank | 52.9% |
| cop_focal_mean_3000m_mean_cityrank | 52.9% |
| cop_focal_mean_3000m_max_cityrank | 52.9% |
| cop_focal_min_3000m_mean_cityrank | 52.9% |
| cop_focal_min_3000m_max_cityrank | 52.9% |
| cop_rel_elev_3000m_min_cityrank | 52.9% |
| cop_slope_max_cityrank | 52.9% |
| cop_elevation_percentile_1km_mean_cityrank | 52.9% |
| cop_elevation_percentile_1km_max_cityrank | 52.9% |
| cop_slope_mean_cityrank | 52.9% |
| cop_fill_depth_mean_cityrank | 52.9% |
| cop_fill_depth_min_cityrank | 52.9% |
| cop_focal_mean_1000m_max_cityrank | 52.9% |
| cop_twi_mean_cityrank | 52.9% |
| cop_twi_max_cityrank | 52.9% |
| cop_fill_share_gt_0_2m_cityrank | 52.9% |
| cop_fill_depth_max_cityrank | 52.9% |
| cop_dist_water_any_m_min_cityrank | 52.9% |
| cop_dist_water_any_m_mean_cityrank | 52.9% |
| cop_dist_water_major_m_min_cityrank | 52.9% |
| cop_dist_water_major_m_mean_cityrank | 52.9% |
| cop_elevation_max_cityrank | 52.9% |
| cop_elevation_mean_cityrank | 52.9% |
| cop_elevation_range_cityrank | 52.9% |
| n_ways_cityrank | 52.9% |
| road_intersections_300m_cityrank | 52.9% |
| length_m_cityrank | 52.9% |
| bridge_frac_cityrank | 52.9% |
| tunnel_frac_cityrank | 52.9% |
| road_length_density_500m_cityrank | 52.9% |
| road_highway_rank | 2.4% |
| fab_hand_major_m_mean | 0.3% |
| fab_hand_major_m_min | 0.3% |
| cop_hand_major_m_mean | 0.2% |
| cop_hand_major_m_min | 0.2% |
| fab_hand_any_m_min | 0.1% |
| fab_hand_any_m_mean | 0.1% |
| cop_hand_any_m_min | 0.1% |
| cop_hand_any_m_mean | 0.1% |
| lc_grass_shrub_500m_frac | 0.1% |
| lc_grass_shrub_200m_frac | 0.1% |
| lc_tree_200m_frac | 0.1% |
| lc_tree_500m_frac | 0.1% |
| lc_builtup_500m_frac | 0.1% |
| lc_builtup_200m_frac | 0.1% |
| lc_bare_500m_frac | 0.1% |
| lc_bare_200m_frac | 0.1% |
| lc_water_500m_frac | 0.1% |
| lc_water_200m_frac | 0.1% |
| lc_cropland_200m_frac | 0.1% |
| lc_cropland_500m_frac | 0.1% |
| lc_wetland_mangrove_500m_frac | 0.1% |
| lc_wetland_mangrove_200m_frac | 0.1% |
| fab_focal_mean_300m_max | 0.1% |
| fab_focal_min_300m_mean | 0.1% |
| fab_focal_min_300m_max | 0.1% |
| fab_rel_elev_300m_min | 0.1% |
| fab_focal_mean_3000m_mean | 0.1% |
| fab_rel_elev_1000m_mean | 0.1% |
| fab_rel_elev_1000m_min | 0.1% |
| fab_focal_min_1000m_max | 0.1% |
| fab_elevation_range | 0.1% |
| fab_elevation_min | 0.1% |
| fab_elevation_p10 | 0.1% |
| fab_elevation_mean | 0.1% |
| fab_rel_elev_300m_mean | 0.1% |
| fab_focal_mean_1000m_mean | 0.1% |
| fab_elevation_max | 0.1% |
| fab_focal_mean_300m_mean | 0.1% |
| fab_focal_min_1000m_mean | 0.1% |
| fab_focal_mean_1000m_max | 0.1% |
| fab_focal_min_3000m_mean | 0.1% |
| fab_focal_mean_3000m_max | 0.1% |
| fab_dist_water_major_m_min | 0.1% |
| fab_twi_max | 0.1% |
| fab_dist_water_any_m_min | 0.1% |
| fab_dist_water_any_m_mean | 0.1% |
| fab_elevation_percentile_1km_mean | 0.1% |
| fab_elevation_percentile_1km_max | 0.1% |
| fab_rel_elev_3000m_mean | 0.1% |
| fab_slope_max | 0.1% |
| fab_flow_accumulation_log_mean | 0.1% |
| fab_flow_accumulation_log_max | 0.1% |
| fab_fill_share_gt_0_2m | 0.1% |
| fab_fill_depth_max | 0.1% |
| fab_focal_min_3000m_max | 0.1% |
| fab_rel_elev_3000m_min | 0.1% |
| fab_fill_depth_min | 0.1% |
| fab_dist_water_major_m_mean | 0.1% |
| fab_dist_any_water_min | 0.1% |
| fab_fill_depth_mean | 0.1% |
| fab_slope_mean | 0.1% |
| fab_twi_mean | 0.1% |
| fab_elev_min | 0.1% |
| cop_elevation_mean | 0.0% |
| cop_elevation_min | 0.0% |
| cop_elevation_max | 0.0% |
| cop_focal_mean_300m_max | 0.0% |
| cop_elevation_p10 | 0.0% |
| cop_dist_water_major_m_min | 0.0% |
| cop_dist_water_major_m_mean | 0.0% |
| cop_fill_share_gt_0_2m | 0.0% |
| cop_fill_depth_max | 0.0% |
| cop_dist_water_any_m_mean | 0.0% |
| cop_dist_water_any_m_min | 0.0% |
| cop_flow_accumulation_log_mean | 0.0% |
| cop_focal_mean_300m_mean | 0.0% |
| cop_slope_mean | 0.0% |
| cop_slope_max | 0.0% |
| cop_focal_mean_3000m_max | 0.0% |
| cop_focal_mean_3000m_mean | 0.0% |
| cop_rel_elev_1000m_mean | 0.0% |
| cop_rel_elev_1000m_min | 0.0% |
| cop_rel_elev_3000m_mean | 0.0% |
| cop_rel_elev_3000m_min | 0.0% |
| cop_elevation_range | 0.0% |
| cop_rel_elev_300m_mean | 0.0% |
| cop_focal_min_300m_mean | 0.0% |
| cop_focal_min_300m_max | 0.0% |
| cop_focal_mean_1000m_max | 0.0% |
| cop_focal_mean_1000m_mean | 0.0% |
| cop_rel_elev_300m_min | 0.0% |
| cop_flow_accumulation_log_max | 0.0% |
| cop_twi_mean | 0.0% |
| cop_twi_max | 0.0% |
| cop_focal_min_1000m_max | 0.0% |
| cop_focal_min_1000m_mean | 0.0% |
| cop_fill_depth_mean | 0.0% |
| cop_fill_depth_min | 0.0% |
| cop_elevation_percentile_1km_mean | 0.0% |
| cop_elevation_percentile_1km_max | 0.0% |
| cop_focal_min_3000m_max | 0.0% |
| cop_focal_min_3000m_mean | 0.0% |
| length_m | 0.0% |
| tunnel_frac | 0.0% |
| named | 0.0% |
| n_ways | 0.0% |
| bridge_frac | 0.0% |
| road_highway_class | 0.0% |
| road_length_density_500m | 0.0% |
| road_intersections_300m | 0.0% |
### Interpretable feature summaries
| Feature | Non-null | Mean | Median | P10–P90 |
|---|---:|---:|---:|---:|
| fab_elev_min | 140158 | 9.105 | 5.387 | 1.964–24.356 |
| cop_elevation_min | 140189 | 10.891 | 7.624 | 2.757–26.170 |
| fab_rel_elev_1000m_min | 140158 | -0.133 | -0.054 | -2.308–1.898 |
| fab_fill_depth_max | 140158 | 0.038 | 0.000 | 0.000–0.096 |
| fab_flow_accumulation_log_max | 140158 | 1.678 | 1.609 | 1.099–2.639 |
| fab_twi_max | 140158 | 10.391 | 10.305 | 8.584–12.355 |
| fab_dist_any_water_min | 140158 | 448.086 | 318.904 | 30.000–1053.423 |
| fab_hand_any_m_min | 140045 | 1.794 | 0.370 | -0.693–6.309 |
| lc_builtup_200m_frac | 140139 | 0.707 | 0.822 | 0.204–0.991 |
| lc_water_500m_frac | 140139 | 0.028 | 0.000 | 0.000–0.099 |
| road_length_density_500m | 140236 | 0.021 | 0.021 | 0.008–0.034 |
| road_intersections_300m | 140236 | 50.764 | 34.000 | 6.000–124.000 |
### rain univariate ranking (positive routes: 178)

| Rank | Feature | Better direction | ROC AUC (95% CI) | Recall at 10% |
|---:|---|---|---:|---:|
| 1 | road_highway_rank | high | 0.857 (0.827–0.887) | 73.4% |
| 2 | road_highway_rank_cityrank | high | 0.857 (0.825–0.882) | 73.4% |
| 3 | road_intersections_300m | high | 0.763 (0.739–0.786) | 20.8% |
| 4 | road_intersections_300m_cityrank | high | 0.763 (0.735–0.784) | 20.8% |
| 5 | lc_grass_shrub_500m_frac | low | 0.760 (0.734–0.784) | 27.0% |
| 6 | lc_grass_shrub_500m_frac_cityrank | low | 0.760 (0.736–0.791) | 27.0% |
| 7 | road_length_density_500m | high | 0.748 (0.718–0.775) | 28.7% |
| 8 | road_length_density_500m_cityrank | high | 0.748 (0.718–0.774) | 28.7% |
| 9 | cop_fill_depth_max | high | 0.745 (0.711–0.782) | 38.2% |
| 10 | cop_fill_depth_max_cityrank | high | 0.745 (0.696–0.783) | 38.2% |
| 11 | lc_cropland_500m_frac | low | 0.739 (0.711–0.761) | 21.3% |
| 12 | lc_cropland_500m_frac_cityrank | low | 0.739 (0.710–0.770) | 21.3% |
| 13 | lc_builtup_500m_frac | high | 0.735 (0.714–0.755) | 22.5% |
| 14 | lc_builtup_500m_frac_cityrank | high | 0.735 (0.707–0.757) | 22.5% |
| 15 | cop_rel_elev_300m_min | low | 0.735 (0.702–0.773) | 34.8% |

Bottom five by oriented AUC: cop_focal_mean_3000m_mean 0.503 [0.475, 0.534]; cop_focal_mean_3000m_mean_cityrank 0.503 [0.473, 0.536]; cop_hand_major_m_mean 0.504 [0.470, 0.538]; cop_hand_major_m_mean_cityrank 0.504 [0.469, 0.538]; lc_wetland_mangrove_200m_frac 0.504 [0.504, 0.504].
Design baselines: lowest FABDEM elevation: AUC 0.568 [0.532, 0.604], recall_at_10pct 12.4%, direction low; proximity to any water: AUC 0.625 [0.584, 0.657], recall_at_10pct 18.0%, direction low.

### tide univariate ranking (positive routes: 151)

| Rank | Feature | Better direction | ROC AUC (95% CI) | Recall at 10% |
|---:|---|---|---:|---:|
| 1 | cop_dist_water_major_m_min | low | 0.834 (0.809–0.854) | 43.0% |
| 2 | cop_dist_water_major_m_min_cityrank | low | 0.834 (0.814–0.854) | 43.0% |
| 3 | fab_dist_water_major_m_min | low | 0.834 (0.812–0.856) | 43.0% |
| 4 | fab_dist_water_major_m_min_cityrank | low | 0.834 (0.812–0.854) | 43.0% |
| 5 | cop_dist_water_any_m_min | low | 0.821 (0.799–0.845) | 33.8% |
| 6 | cop_dist_water_any_m_min_cityrank | low | 0.821 (0.797–0.849) | 33.8% |
| 7 | fab_dist_water_any_m_min | low | 0.821 (0.795–0.840) | 35.8% |
| 8 | fab_dist_any_water_min | low | 0.821 (0.793–0.839) | 35.8% |
| 9 | fab_dist_water_any_m_min_cityrank | low | 0.821 (0.803–0.841) | 35.8% |
| 10 | fab_dist_any_water_min_cityrank | low | 0.821 (0.793–0.842) | 35.8% |
| 11 | cop_dist_water_major_m_mean | low | 0.808 (0.786–0.832) | 33.8% |
| 12 | cop_dist_water_major_m_mean_cityrank | low | 0.808 (0.785–0.830) | 33.8% |
| 13 | fab_dist_water_major_m_mean | low | 0.808 (0.783–0.828) | 33.8% |
| 14 | fab_dist_water_major_m_mean_cityrank | low | 0.808 (0.780–0.828) | 33.8% |
| 15 | cop_focal_min_300m_mean | low | 0.802 (0.775–0.832) | 31.8% |

Bottom five by oriented AUC: lc_bare_500m_frac 0.500 [0.458, 0.535]; lc_bare_500m_frac_cityrank 0.500 [0.462, 0.529]; lc_wetland_mangrove_200m_frac 0.501 [0.494, 0.504]; lc_wetland_mangrove_200m_frac_cityrank 0.501 [0.494, 0.504]; cop_fill_depth_min 0.501 [0.487, 0.519].
Design baselines: lowest FABDEM elevation: AUC 0.757 [0.725, 0.781], recall_at_10pct 27.8%, direction low; proximity to any water: AUC 0.821 [0.793, 0.839], recall_at_10pct 35.8%, direction low.

## da_nang

- Routes with features: 21429; in modelling universe: 14023; feature columns excluding key and flag: 222.
- Highest feature null rates: lanes_cityrank 87.2%, lanes 84.7%, road_highway_rank_cityrank 35.5%, fab_hand_major_m_mean_cityrank 34.7%, fab_hand_major_m_min_cityrank 34.7%, cop_hand_major_m_min_cityrank 34.7%, cop_hand_major_m_mean_cityrank 34.7%, fab_hand_any_m_min_cityrank 34.6%, fab_hand_any_m_mean_cityrank 34.6%, cop_hand_any_m_mean_cityrank 34.6%.

### Null rate by continuous feature

| Feature | Null rate |
|---|---:|
| lanes_cityrank | 87.2% |
| lanes | 84.7% |
| road_highway_rank_cityrank | 35.5% |
| fab_hand_major_m_mean_cityrank | 34.7% |
| fab_hand_major_m_min_cityrank | 34.7% |
| cop_hand_major_m_min_cityrank | 34.7% |
| cop_hand_major_m_mean_cityrank | 34.7% |
| fab_hand_any_m_min_cityrank | 34.6% |
| fab_hand_any_m_mean_cityrank | 34.6% |
| cop_hand_any_m_mean_cityrank | 34.6% |
| cop_hand_any_m_min_cityrank | 34.6% |
| lc_tree_500m_frac_cityrank | 34.6% |
| lc_tree_200m_frac_cityrank | 34.6% |
| lc_water_500m_frac_cityrank | 34.6% |
| lc_bare_200m_frac_cityrank | 34.6% |
| lc_bare_500m_frac_cityrank | 34.6% |
| lc_water_200m_frac_cityrank | 34.6% |
| lc_wetland_mangrove_200m_frac_cityrank | 34.6% |
| lc_grass_shrub_200m_frac_cityrank | 34.6% |
| lc_grass_shrub_500m_frac_cityrank | 34.6% |
| lc_cropland_200m_frac_cityrank | 34.6% |
| lc_cropland_500m_frac_cityrank | 34.6% |
| lc_builtup_200m_frac_cityrank | 34.6% |
| lc_builtup_500m_frac_cityrank | 34.6% |
| lc_wetland_mangrove_500m_frac_cityrank | 34.6% |
| cop_rel_elev_300m_min_cityrank | 34.6% |
| cop_focal_min_300m_max_cityrank | 34.6% |
| cop_focal_min_300m_mean_cityrank | 34.6% |
| cop_focal_mean_300m_max_cityrank | 34.6% |
| cop_focal_mean_300m_mean_cityrank | 34.6% |
| fab_elevation_percentile_1km_mean_cityrank | 34.6% |
| fab_rel_elev_3000m_mean_cityrank | 34.6% |
| fab_focal_min_300m_max_cityrank | 34.6% |
| fab_rel_elev_300m_min_cityrank | 34.6% |
| fab_focal_mean_1000m_max_cityrank | 34.6% |
| fab_focal_min_1000m_mean_cityrank | 34.6% |
| fab_rel_elev_300m_mean_cityrank | 34.6% |
| fab_focal_mean_1000m_mean_cityrank | 34.6% |
| fab_rel_elev_1000m_mean_cityrank | 34.6% |
| fab_focal_mean_3000m_mean_cityrank | 34.6% |
| fab_focal_mean_3000m_max_cityrank | 34.6% |
| fab_focal_min_3000m_mean_cityrank | 34.6% |
| fab_focal_min_3000m_max_cityrank | 34.6% |
| fab_rel_elev_3000m_min_cityrank | 34.6% |
| fab_focal_min_1000m_max_cityrank | 34.6% |
| fab_rel_elev_1000m_min_cityrank | 34.6% |
| fab_elevation_max_cityrank | 34.6% |
| fab_elevation_mean_cityrank | 34.6% |
| fab_elevation_percentile_1km_max_cityrank | 34.6% |
| fab_slope_mean_cityrank | 34.6% |
| cop_elevation_p10_cityrank | 34.6% |
| cop_elevation_mean_cityrank | 34.6% |
| fab_dist_water_major_m_min_cityrank | 34.6% |
| fab_dist_water_any_m_mean_cityrank | 34.6% |
| fab_fill_depth_min_cityrank | 34.6% |
| fab_slope_max_cityrank | 34.6% |
| fab_twi_max_cityrank | 34.6% |
| fab_dist_water_any_m_min_cityrank | 34.6% |
| fab_twi_mean_cityrank | 34.6% |
| fab_flow_accumulation_log_max_cityrank | 34.6% |
| fab_fill_share_gt_0_2m_cityrank | 34.6% |
| fab_flow_accumulation_log_mean_cityrank | 34.6% |
| fab_elevation_p10_cityrank | 34.6% |
| fab_elevation_min_cityrank | 34.6% |
| fab_focal_mean_300m_mean_cityrank | 34.6% |
| fab_elevation_range_cityrank | 34.6% |
| fab_fill_depth_mean_cityrank | 34.6% |
| fab_fill_depth_max_cityrank | 34.6% |
| fab_focal_mean_300m_max_cityrank | 34.6% |
| fab_focal_min_300m_mean_cityrank | 34.6% |
| cop_elevation_min_cityrank | 34.6% |
| fab_dist_water_major_m_mean_cityrank | 34.6% |
| cop_flow_accumulation_log_mean_cityrank | 34.6% |
| cop_flow_accumulation_log_max_cityrank | 34.6% |
| cop_dist_water_major_m_mean_cityrank | 34.6% |
| cop_dist_water_major_m_min_cityrank | 34.6% |
| cop_focal_mean_1000m_mean_cityrank | 34.6% |
| cop_focal_mean_1000m_max_cityrank | 34.6% |
| cop_focal_min_1000m_mean_cityrank | 34.6% |
| cop_focal_min_1000m_max_cityrank | 34.6% |
| cop_rel_elev_1000m_min_cityrank | 34.6% |
| cop_rel_elev_1000m_mean_cityrank | 34.6% |
| cop_focal_mean_3000m_mean_cityrank | 34.6% |
| cop_focal_mean_3000m_max_cityrank | 34.6% |
| cop_focal_min_3000m_mean_cityrank | 34.6% |
| cop_focal_min_3000m_max_cityrank | 34.6% |
| cop_rel_elev_3000m_min_cityrank | 34.6% |
| cop_rel_elev_3000m_mean_cityrank | 34.6% |
| cop_elevation_percentile_1km_mean_cityrank | 34.6% |
| cop_elevation_percentile_1km_max_cityrank | 34.6% |
| cop_slope_mean_cityrank | 34.6% |
| cop_slope_max_cityrank | 34.6% |
| cop_fill_depth_min_cityrank | 34.6% |
| cop_fill_depth_mean_cityrank | 34.6% |
| cop_twi_mean_cityrank | 34.6% |
| cop_twi_max_cityrank | 34.6% |
| cop_fill_share_gt_0_2m_cityrank | 34.6% |
| cop_fill_depth_max_cityrank | 34.6% |
| fab_elev_min_cityrank | 34.6% |
| fab_dist_any_water_min_cityrank | 34.6% |
| cop_dist_water_any_m_min_cityrank | 34.6% |
| cop_dist_water_any_m_mean_cityrank | 34.6% |
| cop_elevation_max_cityrank | 34.6% |
| cop_rel_elev_300m_mean_cityrank | 34.6% |
| cop_elevation_range_cityrank | 34.6% |
| n_ways_cityrank | 34.6% |
| road_intersections_300m_cityrank | 34.6% |
| length_m_cityrank | 34.6% |
| bridge_frac_cityrank | 34.6% |
| tunnel_frac_cityrank | 34.6% |
| road_length_density_500m_cityrank | 34.6% |
| road_highway_rank | 2.7% |
| fab_hand_major_m_mean | 0.2% |
| fab_hand_major_m_min | 0.2% |
| cop_hand_major_m_mean | 0.2% |
| cop_hand_major_m_min | 0.2% |
| fab_hand_any_m_min | 0.1% |
| fab_hand_any_m_mean | 0.1% |
| cop_hand_any_m_min | 0.1% |
| cop_hand_any_m_mean | 0.1% |
| lc_grass_shrub_500m_frac | 0.1% |
| lc_grass_shrub_200m_frac | 0.1% |
| lc_tree_200m_frac | 0.1% |
| lc_tree_500m_frac | 0.1% |
| lc_builtup_500m_frac | 0.1% |
| lc_builtup_200m_frac | 0.1% |
| lc_bare_500m_frac | 0.1% |
| lc_bare_200m_frac | 0.1% |
| lc_water_500m_frac | 0.1% |
| lc_water_200m_frac | 0.1% |
| lc_cropland_200m_frac | 0.1% |
| lc_cropland_500m_frac | 0.1% |
| lc_wetland_mangrove_500m_frac | 0.1% |
| lc_wetland_mangrove_200m_frac | 0.1% |
| fab_focal_mean_300m_max | 0.0% |
| fab_focal_min_300m_mean | 0.0% |
| fab_focal_min_300m_max | 0.0% |
| fab_rel_elev_300m_min | 0.0% |
| cop_flow_accumulation_log_mean | 0.0% |
| cop_flow_accumulation_log_max | 0.0% |
| cop_twi_mean | 0.0% |
| cop_twi_max | 0.0% |
| cop_focal_mean_3000m_max | 0.0% |
| cop_focal_mean_3000m_mean | 0.0% |
| cop_rel_elev_1000m_mean | 0.0% |
| cop_rel_elev_1000m_min | 0.0% |
| fab_rel_elev_300m_mean | 0.0% |
| fab_focal_mean_1000m_mean | 0.0% |
| cop_dist_water_major_m_min | 0.0% |
| cop_dist_water_major_m_mean | 0.0% |
| cop_fill_share_gt_0_2m | 0.0% |
| cop_fill_depth_max | 0.0% |
| cop_dist_water_any_m_mean | 0.0% |
| cop_dist_water_any_m_min | 0.0% |
| cop_focal_min_300m_mean | 0.0% |
| cop_focal_min_300m_max | 0.0% |
| cop_rel_elev_300m_min | 0.0% |
| cop_rel_elev_300m_mean | 0.0% |
| fab_slope_mean | 0.0% |
| fab_fill_depth_mean | 0.0% |
| fab_fill_depth_min | 0.0% |
| fab_twi_mean | 0.0% |
| cop_focal_mean_300m_max | 0.0% |
| cop_focal_mean_300m_mean | 0.0% |
| fab_elevation_max | 0.0% |
| fab_focal_mean_300m_mean | 0.0% |
| fab_focal_min_1000m_mean | 0.0% |
| fab_focal_mean_1000m_max | 0.0% |
| fab_focal_min_3000m_mean | 0.0% |
| fab_focal_mean_3000m_max | 0.0% |
| fab_focal_mean_3000m_mean | 0.0% |
| fab_rel_elev_1000m_mean | 0.0% |
| fab_rel_elev_1000m_min | 0.0% |
| fab_focal_min_1000m_max | 0.0% |
| fab_elevation_range | 0.0% |
| fab_elevation_min | 0.0% |
| fab_elevation_p10 | 0.0% |
| fab_elevation_mean | 0.0% |
| cop_rel_elev_3000m_mean | 0.0% |
| cop_rel_elev_3000m_min | 0.0% |
| cop_focal_min_3000m_max | 0.0% |
| cop_focal_min_3000m_mean | 0.0% |
| cop_focal_min_1000m_max | 0.0% |
| cop_focal_min_1000m_mean | 0.0% |
| cop_fill_depth_mean | 0.0% |
| cop_fill_depth_min | 0.0% |
| cop_elevation_percentile_1km_mean | 0.0% |
| cop_elevation_percentile_1km_max | 0.0% |
| cop_slope_mean | 0.0% |
| cop_slope_max | 0.0% |
| fab_elevation_percentile_1km_mean | 0.0% |
| fab_elevation_percentile_1km_max | 0.0% |
| fab_rel_elev_3000m_mean | 0.0% |
| fab_slope_max | 0.0% |
| fab_flow_accumulation_log_mean | 0.0% |
| fab_flow_accumulation_log_max | 0.0% |
| cop_elevation_range | 0.0% |
| cop_elevation_max | 0.0% |
| cop_elevation_mean | 0.0% |
| cop_elevation_p10 | 0.0% |
| cop_elevation_min | 0.0% |
| fab_dist_water_major_m_mean | 0.0% |
| fab_dist_water_major_m_min | 0.0% |
| fab_twi_max | 0.0% |
| fab_dist_water_any_m_min | 0.0% |
| fab_dist_water_any_m_mean | 0.0% |
| fab_focal_min_3000m_max | 0.0% |
| fab_rel_elev_3000m_min | 0.0% |
| cop_focal_mean_1000m_max | 0.0% |
| cop_focal_mean_1000m_mean | 0.0% |
| fab_dist_any_water_min | 0.0% |
| fab_elev_min | 0.0% |
| fab_fill_share_gt_0_2m | 0.0% |
| fab_fill_depth_max | 0.0% |
| length_m | 0.0% |
| tunnel_frac | 0.0% |
| named | 0.0% |
| n_ways | 0.0% |
| bridge_frac | 0.0% |
| road_highway_class | 0.0% |
| road_length_density_500m | 0.0% |
| road_intersections_300m | 0.0% |
### Interpretable feature summaries
| Feature | Non-null | Mean | Median | P10–P90 |
|---|---:|---:|---:|---:|
| fab_elev_min | 21422 | 8.770 | 6.225 | 2.566–11.310 |
| cop_elevation_min | 21422 | 9.294 | 6.609 | 2.564–12.491 |
| fab_rel_elev_1000m_min | 21422 | -2.266 | 0.062 | -7.010–2.239 |
| fab_fill_depth_max | 21422 | 0.053 | 0.000 | 0.000–0.090 |
| fab_flow_accumulation_log_max | 21422 | 1.515 | 1.386 | 1.099–2.079 |
| fab_twi_max | 21422 | 9.884 | 9.900 | 8.271–11.463 |
| fab_dist_any_water_min | 21422 | 382.013 | 276.586 | 30.000–891.964 |
| fab_hand_any_m_min | 21406 | 1.682 | 0.663 | -1.095–4.803 |
| lc_builtup_200m_frac | 21418 | 0.571 | 0.627 | 0.071–0.982 |
| lc_water_500m_frac | 21418 | 0.064 | 0.012 | 0.000–0.219 |
| road_length_density_500m | 21429 | 0.017 | 0.017 | 0.005–0.028 |
| road_intersections_300m | 21429 | 27.270 | 18.000 | 3.000–64.000 |
### rain univariate ranking (positive routes: 395)

| Rank | Feature | Better direction | ROC AUC (95% CI) | Recall at 10% |
|---:|---|---|---:|---:|
| 1 | lc_builtup_500m_frac | high | 0.766 (0.739–0.785) | 30.4% |
| 2 | lc_builtup_500m_frac_cityrank | high | 0.766 (0.746–0.781) | 30.4% |
| 3 | road_intersections_300m | high | 0.762 (0.741–0.783) | 30.9% |
| 4 | road_intersections_300m_cityrank | high | 0.762 (0.738–0.780) | 30.9% |
| 5 | lc_builtup_200m_frac | high | 0.756 (0.733–0.772) | 32.9% |
| 6 | lc_builtup_200m_frac_cityrank | high | 0.756 (0.737–0.779) | 32.9% |
| 7 | road_length_density_500m | high | 0.743 (0.723–0.766) | 26.8% |
| 8 | road_length_density_500m_cityrank | high | 0.743 (0.723–0.762) | 26.8% |
| 9 | lc_grass_shrub_500m_frac | low | 0.742 (0.718–0.757) | 31.4% |
| 10 | lc_grass_shrub_500m_frac_cityrank | low | 0.742 (0.720–0.764) | 31.4% |
| 11 | lc_grass_shrub_200m_frac | low | 0.735 (0.717–0.760) | 32.2% |
| 12 | lc_grass_shrub_200m_frac_cityrank | low | 0.735 (0.714–0.757) | 32.2% |
| 13 | lc_cropland_500m_frac | low | 0.704 (0.686–0.727) | 23.5% |
| 14 | lc_cropland_500m_frac_cityrank | low | 0.704 (0.683–0.725) | 23.5% |
| 15 | cop_fill_depth_max | high | 0.694 (0.669–0.714) | 30.9% |

Bottom five by oriented AUC: tunnel_frac 0.500 [0.498, 0.504]; tunnel_frac_cityrank 0.500 [0.498, 0.503]; fab_rel_elev_1000m_min 0.501 [0.465, 0.526]; fab_rel_elev_1000m_min_cityrank 0.501 [0.474, 0.523]; fab_fill_depth_min 0.502 [0.494, 0.509].
Design baselines: lowest FABDEM elevation: AUC 0.514 [0.493, 0.539], recall_at_10pct 3.3%, direction high; proximity to any water: AUC 0.503 [0.477, 0.531], recall_at_10pct 9.6%, direction high.


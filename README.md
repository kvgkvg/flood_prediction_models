# Flood risk per road, per hour — HCMC and Da Nang

Models behind a road-flood risk layer for a map app: for every road in a city, how likely it is to be flooded at a given hour, so a router can avoid it and users can be warned 1–2 hours ahead.

The design is in [`2026-10-04-du-bao-nguy-co-ngap-duong-design.md`](2026-10-04-du-bao-nguy-co-ngap-duong-design.md) (Vietnamese). This README covers how to get the data, rebuild the models, and what the results say.

## How it works

Risk for a road at a given time is the product of two things:

- **S — how flood-prone the road is** (Model 1). A LightGBM model on terrain, distance to water and land cover. It takes no coordinates, names or ward ids, so it can be applied to a city with no flood records. Roads with a recorded flood before the cutoff are ranked above the model's predictions.
- **T — whether rain or tide is high enough right now** (Model 2). The rain trigger works on percentiles of each city's own rain climate, so one trigger serves every city. The tide trigger uses astronomical tide at Vung Tau (HCMC only).

```
P = 1 − (1 − S_rain × T_rain) × (1 − S_tide × T_tide)
```

Three risk levels come from a two-factor rule: the day state (quiet / watch / alert, from T) and the road's rank (top 5%, next 15%, rest, from S).

A "road" here is a route: OSM ways with the same name inside the same ward. HCMC has 140,236 routes and Da Nang 21,429; the modelled universe excludes service roads and routes under 30 m (66,017 and 14,023 routes).

## Setup

Python 3.14 was used; 14 GB of RAM is enough. Everything runs on CPU.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/pytest -q          # data-dependent tests need the steps below first
```

All commands below are run from the repo root with `PYTHONPATH=src`. They are the commands used to build the committed models; they have not been re-run from a fresh clone, so expect to fix a path or two.

## 1. Download data

Nothing under `data/` is committed. Each script caches to `data/raw/` and skips what is already on disk. Total is under 1 GB.

```bash
export PYTHONPATH=src
.venv/bin/python scripts/download_ird.py               # HCMC flood observations (IRD Dataverse, doi:10.23708/8Y16HU)
.venv/bin/python scripts/download_danang.py            # Da Nang flood reports (public portal API)
.venv/bin/python scripts/download_osm.py --resume-geofabrik   # roads, water, wards from the Geofabrik Vietnam extract (~330 MB)
.venv/bin/python scripts/download_copernicus_dem.py    # Copernicus GLO-30 terrain
.venv/bin/python scripts/download_fabdem.py            # FABDEM terrain (non-commercial licence)
.venv/bin/python scripts/download_worldcover.py        # ESA WorldCover 10 m land cover
.venv/bin/python scripts/download_tide.py              # UHSLC hourly sea level, Vung Tau (station 383)
.venv/bin/python scripts/download_rain.py              # Open-Meteo ERA5 hourly rain, 2002 onward
.venv/bin/python scripts/experiment_rain_sources.py --download   # Open-Meteo ECMWF IFS 9 km rain, 2017–2024
.venv/bin/python scripts/download_locked_ifs.py        # IFS rain for the 2025–2026 test period
.venv/bin/python scripts/make_inventory.py             # writes reports/data_inventory.md
```

Notes:

- **Open-Meteo is rate-limited** (about 5,000 weighted calls per hour, 10,000 per day). `download_rain.py` tracks its own budget and sleeps on HTTP 429; the full ERA5 history takes more than one quota window.
- **Overpass was unreliable**, which is why the OSM step goes straight to the Geofabrik extract.
- **Da Nang portal**: the script calls only the endpoints the public page itself uses, slowly. The portal states no data licence; ask before reusing the data.
- **Licences**: IRD is CC BY-NC 4.0 on the dataset page (its ReadMe says CC BY 4.0); FABDEM is non-commercial.
- City bounding boxes are fixed in `src/floodrisk/cities.py`.

## 2. Build routes, labels and features

One command per city for each step (`ho_chi_minh`, `da_nang`).

```bash
.venv/bin/python scripts/build_flood_records.py        # unified flood record table
for c in ho_chi_minh da_nang; do
  .venv/bin/python scripts/build_routes.py --city $c
done
.venv/bin/python scripts/match_records.py              # flood record -> route, and route labels
for c in ho_chi_minh da_nang; do
  .venv/bin/python scripts/build_terrain.py --city $c --dem fabdem
  .venv/bin/python scripts/build_terrain.py --city $c --dem copernicus
  .venv/bin/python scripts/build_features.py --city $c   # 222 features per route
done
.venv/bin/python scripts/build_drivers.py              # daily rain and tide drivers
```

Flood records dated 2025 or later are a locked test split: they are stored but never used for labels, features or tuning.

## 3. Train and evaluate

```bash
# Model 1: bias-controlled evaluation of any scorer in experiments/m1/
.venv/bin/python scripts/eval_m1.py --scorer lgbm_phys_cityrank
.venv/bin/python scripts/eval_m1.py --scorer all        # every baseline and experiment
.venv/bin/python scripts/make_m1_report.py              # reports/m1_leaderboard.md

# Whole system, rehearsal: fit on data before 2023, test on 2023–2024
.venv/bin/python scripts/fit_final.py --cutoff 2023-01-01 --verify-dev

# Final models: fit on everything before 2025
.venv/bin/python scripts/build_locked_tide.py
.venv/bin/python scripts/fit_final.py --cutoff 2025-01-01    # writes models/final_2025-01-01/
```

Every choice (features, hyperparameters, thresholds, rain source) is in `models/final_config.json`. `scripts/eval_locked.py` scores the 2025–2026 test; it has already been run and refuses to run again without `--force`. Please do not tune against it.

To try a new Model 1 idea, add one file to `experiments/m1/` exposing `fit` and `predict`, and run `eval_m1.py --scorer <name> --baseline lgbm_phys_cityrank`. The harness (`src/floodrisk/evalm1.py`) is frozen by a hash test.

## 4. Export for the web app

```bash
for c in ho_chi_minh da_nang; do
  .venv/bin/python scripts/export_city.py --city $c --model-dir models/final_2025-01-01
  .venv/bin/python scripts/run_hourly.py --city $c --offline-sample   # replay of a cached flood day, no network
done
```

This writes `data/export/<city>/`: `routes.geojson.gz` / `routes.parquet`, `risk_hourly.parquet` / `.json.gz` (now, +1 h, +2 h) and `city_status.json`. Fields are documented in [`reports/data_contract.md`](reports/data_contract.md). `src/floodrisk/evidence.py` holds the functions that adjust a road's risk from user reports.

`run_hourly.py` without `--offline-sample` fetches the live Open-Meteo forecast. That path has only been tested on the offline replay.

## Results

### Model 1: which roads are flood-prone

Flood labels are biased: the press names big roads in HCMC, and citizens report from dense streets in Da Nang. Road class alone "finds" 73% of HCMC rain-flooded roads in the top 10%, which says nothing about water. So the headline metric ranks roads within groups of similar reporting exposure and asks what share of flooded roads land in the top 10% of each group. It is averaged over three tests: train HCMC → test Da Nang, train Da Nang → test HCMC, and HCMC tide with spatial cross-validation.

| Scorer | Top-10% recall, exposure-controlled |
|---|---|
| LightGBM, terrain + water + land cover (chosen) | 0.331 |
| LightGBM, all features | 0.321 |
| LightGBM, the design's original inputs | 0.247 |
| Nearest water | 0.171 |
| Lowest elevation | 0.154 |
| Exposure only | 0.124 |
| Random | 0.098 |

Twelve alternative approaches (bagging over unlabeled roads, exposure-matched negatives, monotone constraints, linear and spline models, ensembles) all failed to beat the chosen model. Model 1 is limited by data, not by model choice.

### Locked test, 2025–2026

Models were fitted on data before 2025 and scored on flood days the models never saw.

| | HCMC (8 flood days, 33 records) | Da Nang (18 flood days, 115 records) |
|---|---|---|
| Flood records on roads in the top 5% | 73% | 36% |
| Flood records on roads in the top 20% | 96% | 59% |
| "Flooded before" list alone, at its own size | 43% | 16% |
| Records on never-recorded roads, top 5% | 55% | 23% |
| Rain trigger: flood days vs other days (AUC) | 0.635 | 0.906 |
| Tide trigger (AUC, 3 tide days) | 0.876 | — |
| Flood days in watch or alert for rain | 12.5% | 94% |
| Flooded roads at medium or high risk | 25% | 45% |
| Same, for the always-on "flooded before" list | 36% | 16% |
| Roads flagged on dry-season days | 1.8% | 1.3% |

With 8 and 18 flood days the intervals are wide; they are in [`reports/locked_eval.md`](reports/locked_eval.md).

## Insights

- **Ranking roads works, including roads nobody had recorded.** Terrain and water features carry real signal across cities once reporting bias is controlled.
- **Check for reporting bias before trusting a flood model.** The naive metric rewards "big road" and "dense area". Rank within exposure groups.
- **A percentile-based rain trigger transfers between cities.** It was fitted almost entirely on HCMC days and reached 0.906 in Da Nang without local tuning.
- **Rain data is the bottleneck in HCMC.** Model rain at 9–28 km does not see local storms: the rain trigger rated most HCMC flood days as quiet. Station or radar rain is the upgrade that matters most. Until then, rely on the road ranking, user reports and the tide trigger there.
- **Tide flooding is predictable days ahead** from astronomical tide alone.
- **A history list is a strong baseline at small scale** and useless for new roads; combining it with the model is better than either.

## Limits

- Roads with no record are not known to be dry, so false-alarm rates are not reported as hard numbers.
- The trigger is fitted on days (records have dates, not hours) and applied to hourly windows.
- 29 of the 115 Da Nang test records could not be matched to a road and are excluded from the road-hit numbers.
- The locked scoring was executed three times because of two reporting bugs; the model and config were frozen throughout (see the report).
- Flood depth and the flooded stretch within a road are not predicted or verified.
- 30 m terrain cannot resolve depth; it is used only for relative features.

More detail: [`reports/model_card.md`](reports/model_card.md), [`reports/m1_leaderboard.md`](reports/m1_leaderboard.md), [`reports/features.md`](reports/features.md), [`reports/routes_and_labels.md`](reports/routes_and_labels.md).

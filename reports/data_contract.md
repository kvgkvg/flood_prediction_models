# Web data contract

All exported files are UTF-8 where textual, are generated under `data/export/<city>/`, and use the frozen `final_2025-01-01` configuration. Risk percentages are unitless probabilities in `[0,1]`; times are local `Asia/Ho_Chi_Minh` unless stated.

## 1. `routes.parquet` and `routes.geojson.gz`

One row/feature per route. Geometry uses EPSG:4326 longitude/latitude. GeoParquet preserves both geometry columns; GeoJSON uses `geometry` for the route and places the nested GeoJSON geometry for `lowest_segment` in the properties object.

| Field | Type / units | Meaning and valid values |
|---|---|---|
| `route_id` | string | Stable route key. |
| `name` | nullable string | OSM route name. |
| `highway_class` | string | Most common OSM vehicle-road class by length. |
| `in_universe` | bool | Model universe flag from the frozen road-class/length rule. |
| `geometry` | LineString/MultiLineString, EPSG:4326 | Route geometry simplified by about 2 m in local UTM. |
| `lowest_segment` | MultiLineString/GeometryCollection, EPSG:4326 | Approximate lowest 20% by sampled FABDEM elevation. |
| `lowest_segment_unverified` | bool | Always true; the low segment is a terrain estimate, not observed flood extent. |
| `S_hyb_rain`, `S_hyb_tide` | float `[0,1]` | Frozen susceptibility plus pre-cutoff history, by cause. |
| `route_state_rain`, `route_state_tide` | `A`/`B`/`C` | Frozen route bands: top 5%, next 15%, remainder. |
| `has_history` | bool | At least one matched pre-2025 flood record of either cause. |
| `n_history_dates` | integer `>=0`, local dates | Distinct pre-2025 matched record dates for the route. |
| `max_recorded_depth_cm` | nullable float, cm | Greatest pre-2025 recorded depth. |
| `depth_class` | `<10`, `10-30`, `>30`, `unknown` | Class of the greatest recorded depth. |
| `depth_provenance` | nullable string | `official_observation` when depth exists; null otherwise. |
| `provenance` | string | `official_observation` for routes with history, else `model_forecast`. |

## 2. `risk_hourly.parquet` and `risk_hourly.json.gz`

Three route rows per run, for the valid time now, +1 h, and +2 h. The hourly implementation applies a day-fitted trigger to trailing hourly windows; this is an operational approximation and has not been separately calibrated.

| Field | Type / units | Meaning and valid values |
|---|---|---|
| `route_id` | string | Join key to route export. |
| `valid_time` | timestamp, local timezone | Forecast/replay target time. |
| `horizon_h` | integer `0..2`, hours | Forecast lead. |
| `P` | float `[0,1]` | Combined route risk: `1-(1-S_rain*T_rain)(1-S_tide*T_tide)`. |
| `level` | `low`/`medium`/`high` | Frozen two-factor route-band/day-state rule. |
| `S_rain`, `S_tide` | float `[0,1]` | Hybrid route susceptibility used in `P`. |
| `T_rain`, `T_tide` | float `[0,1]` | Rain/tide trigger values. Da Nang tide trigger is zero. |
| `day_state_rain`, `day_state_tide` | `quiet`/`watch`/`alert` | State after frozen thresholds. |
| `provenance` | string | `model_forecast`, or `official_observation` when the route has history. |
| `active_report_count` | integer `>=0` | Placeholder, currently zero; live evidence is a separate updater. |
| `max_recorded_depth_cm` | nullable float, cm | Greatest pre-2025 route record depth. |

## 3. `city_status.json`

| Field | Type / units | Meaning and valid values |
|---|---|---|
| `city` | string | City slug. |
| `confidence` | `verified` / `estimated_unverified` | Verified only when a locked evaluation exists with flood days/records for that city. |
| `model_version` | string | `final_2025-01-01`. |
| `rain_source` | string | IFS percentile input; frozen configuration specifies ERA5 percentile fallback if IFS is missing. |
| `generated_at` | ISO timestamp | Export creation time, local timezone. |
| `offline_sample` | bool | True for cached historical replay. |
| `sample_at` | nullable ISO timestamp | Replay time, if offline. |
| `weather_source` | string | Forecast endpoint/model or cached replay file. |
| `locked_evaluation_attached` | bool | Whether held-out evaluation numbers exist for this city. |

## Example rows

Route example: `route_id=...`, `highway_class=residential`, `in_universe=true`, `S_hyb_rain=0.93`, `route_state_rain=A`, `has_history=true`, `max_recorded_depth_cm=null`, `lowest_segment_unverified=true`.

Risk example: `route_id=...`, `horizon_h=1`, `P=0.42`, `level=medium`, `T_rain=0.61`, `T_tide=0.08`, `day_state_rain=alert`, `active_report_count=0`.

City status example: `{"city":"da_nang","confidence":"verified","model_version":"final_2025-01-01","offline_sample":true}`.

## Live evidence updater

`floodrisk.evidence.update_probability()` consumes user/route/time/status records and applies multiplicative odds evidence with 30-minute half-life decay. Official flooded reports use odds ×10; other flooded reports ×3; not-flooded reports ÷3. A user contributes at most one report per route in each 30-minute window. `displayed_level()` returns the most frequent active status/depth class. The runner currently exports `active_report_count=0`; the web service supplies live records to this pure updater.

# Kiểm kê dữ liệu thực tế

Generated from local files; raw root `data/raw` and interim root `data/interim`.

## data/interim/dem

No files present.

## data/raw/ird_hcmc

- `data/raw/ird_hcmc/Flood_event_locations.tab` — 96,977 B (0.09 MiB)
- `data/raw/ird_hcmc/HCMC_Floods_BDD.gpkg` — 249,856 B (0.24 MiB)
  - Layer Flood_event_locations: 425 rows; CRS EPSG:9210; columns/nulls: Obs_id=0, Date=63, Year=0, Location_name=0, Location_type=0, District_mentioned=7, Ward=47, Current_admin_unit=5, Water_height_max_cm=278, Depth_class=0, Cause=0, Impact_type=0, Source_id=0, Source_type=0, Spatial_precision=0, Geocoding_method=0, Observation_notes=357, Commune=397, Province=418, Water_height_min_cm=314, Duration_hours=398
- `data/raw/ird_hcmc/HCMC_Roads.gpkg` — 131,072 B (0.12 MiB)
  - Layer Flood_recurrence_by_street: 9 rows; CRS EPSG:9210; columns/nulls: road_name=0, Mentioned_years=0
- `data/raw/ird_hcmc/HCMC_new_limits.gpkg` — 507,904 B (0.48 MiB)
  - Layer Limits_before_2025_administrative_reform__: 4 rows; CRS PROJCS["HCM-VN2000",GEOGCS["GCS_VN_2000",DATUM["Vietnam_2000",SPHEROID["WGS_1984",6378137,298.257223563],AUTHORITY["EPSG","6756"]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433],AUTHORITY["EPSG","4756"]],PROJECTION["Transverse_Mercator"],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],PARAMETER["central_meridian",105.75],PARAMETER["scale_factor",0.9999],PARAMETER["latitude_of_origin",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]; columns/nulls: GhiChu=0, TinhCu=0, Shape_Leng=0, POP=0
- `data/raw/ird_hcmc/HCMC_pop_density_districts.gpkg` — 1,142,784 B (1.09 MiB)
  - Layer Population_density_by_district_in_2019: 24 rows; CRS EPSG:9210; columns/nulls: D_Code=0, SUM_TongDans01=0, SUM_Dientich_k=0, Dens_district=0
- `data/raw/ird_hcmc/HCMC_water.gpkg` — 4,243,456 B (4.05 MiB)
  - Layer Rivers__main_canals_and_water_bodies: 2430 rows; CRS EPSG:4326; columns/nulls: FID_1=0, osm_id=0, code=0, fclass=0, name=0
- `data/raw/ird_hcmc/Metadata-form-HCMC-floods.pdf` — 43,338 B (0.04 MiB)
- `data/raw/ird_hcmc/ReadMe_10_23708_8Y16HU.txt` — 1,705 B (0.00 MiB)
- `data/raw/ird_hcmc/Sources_floods_HCMC.tab` — 4,443 B (0.00 MiB)
- `data/raw/ird_hcmc/dataverse_metadata.json` — 19,628 B (0.02 MiB)
- `data/raw/ird_hcmc/industrial_zones_verified.gpkg` — 540,672 B (0.52 MiB)
  - Layer osm_IZ_v2: 735 rows; CRS EPSG:4326; columns/nulls: base_layer=599, name=118, name_fr=710, name_en=627, verif_luz=640, descriptio=671, main_activ=701, category=1, owner=726, brand=734, voltage=734, start_date=711, operator=690, industrial=613, website=707, osm_id=30, surface=727, nb_companies=726

## data/raw/osm

- `data/raw/osm/city_bboxes.json` — 559 B (0.00 MiB)
- `data/raw/osm/da_nang_boundary.json` — 233,334 B (0.22 MiB)
- `data/raw/osm/ho_chi_minh_boundary.json` — 638,759 B (0.61 MiB)

## data/raw/uhslc_vung_tau

- `data/raw/uhslc_vung_tau/uhslc_vung_tau_hourly.csv` — 6,744,156 B (6.43 MiB)
  - 164748 rows; time 2007-10-15 12:00:00+00:00 to 2026-07-31 23:00:00+00:00; columns/nulls: time=0, sea_level=4399, quality=0, station_name=0, uhslc_id=0

## IRD flood-observation audit

- Rows: 425 (design claims 425).
- Date column `Date`; distinct dates 64 (design: 64); undated rows 63 (design: 63); 2025–2026 rows 50 (count only; locked holdout).
- Rows per year (aggregate counts only):
  - 2002: 46
  - 2005: 3
  - 2006: 15
  - 2007: 15
  - 2008: 24
  - 2010: 26
  - 2011: 26
  - 2012: 38
  - 2013: 19
  - 2015: 4
  - 2016: 23
  - 2017: 4
  - 2018: 25
  - 2019: 44
  - 2020: 11
  - 2022: 6
  - 2023: 28
  - 2024: 18
  - 2025: 43
  - 2026: 7
- Cause distribution for pre-2025 rows only (`Cause`); locked holdout excluded:
  - Rain: 180
  - High tide: 149
  - Combined: 46
- Depth availability in pre-2025 rows (`Water_height_max_cm`): 131 populated / 244 null; locked holdout excluded.
- Location precision categories in pre-2025 rows (`Spatial_precision`); locked holdout excluded:
  - Low: 174
  - Medium: 76
  - High: 65
  - Low : 45
  - Medium : 13
  - Hugh: 1
  - Hgh: 1

## Da Nang reports

Portal returned HTTP 403 “Blocked For Attack Detected”; no data downloaded and no bypass attempted. Historical report counts and 2025–2026 count unavailable.

## Design comparison

- IRD observations: design 425; observed 425 — match. Distinct dates: design 64; observed 64 — match. Undated rows: design 63; observed 63 — match.
- IRD cause counts (198 rain / 176 tide / 51 combined), depth-unknown count (257), and full-period precision distribution are design claims. Only pre-2025 attributes are reported above; these claims cannot be compared without inspecting the locked 2025–2026 holdout.
- IRD period: design says 2002–08/2026; aggregate rows exist in Year 2002–2026. Exact latest event date/month is intentionally not reported because the holdout is locked.
- Da Nang: design claims 633 reports, 35 dates, and 392 on 2022-10-14; source returned HTTP 403, so each claim is unverified and no mismatch can be calculated.
- IRD license discrepancy: Dataverse API metadata says CC BY-NC 4.0; downloaded ReadMe says CC BY 4.0. Ask the authors before reuse.

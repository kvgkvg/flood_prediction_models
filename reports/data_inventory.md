# Kiểm kê dữ liệu thực tế

Generated from local files; raw root `data/raw` and interim root `data/interim`.

## data/interim/dem

- Source URL: https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/
- Licence/access note: Copernicus DEM; free/open access, attribution to Copernicus required.

- `data/interim/dem/da_nang_copernicus_glo30.tif` — 2,024,554 B (1.93 MiB)
  - Raster 1081x829; CRS EPSG:4326; bounds (108.0499, 15.92982, 108.35018, 16.1601)
- `data/interim/dem/da_nang_fabdem_v1_2.tif` — 1,248,611 B (1.19 MiB)
  - Raster 1081x829; CRS EPSG:4326; bounds (108.0499, 15.92982, 108.35018, 16.1601)
- `data/interim/dem/ho_chi_minh_copernicus_glo30.tif` — 12,146,455 B (11.58 MiB)
  - Raster 2030x1801; CRS EPSG:4326; bounds (106.43625, 10.54982, 107.00014, 11.0501)
- `data/interim/dem/ho_chi_minh_fabdem_v1_2.tif` — 5,526,659 B (5.27 MiB)
  - Raster 2030x1801; CRS EPSG:4326; bounds (106.43625, 10.54982, 107.00014, 11.0501)

## data/interim/landcover

- `data/interim/landcover/da_nang_ESA_WorldCover_10m_2021_v200_N15E108_Map.tif` — 562,705 B (0.54 MiB)
  - Raster 3600x2760; CRS EPSG:4326; bounds (108.05, 15.93, 108.35, 16.16)
- `data/interim/landcover/ho_chi_minh_ESA_WorldCover_10m_2021_v200_N09E105_Map.tif` — 4,038,301 B (3.85 MiB)
  - Raster 6764x6000; CRS EPSG:4326; bounds (106.43633, 10.55, 107.0, 11.05)

## data/raw/copernicus_dem

- Source URL: https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/
- Licence/access note: Copernicus DEM; free/open access, attribution to Copernicus required.

- `data/raw/copernicus_dem/Copernicus_DSM_COG_10_N10_00_E106_00_DEM.tif` — 46,642,401 B (44.48 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (105.99986, 10.00014, 106.99986, 11.00014)
- `data/raw/copernicus_dem/Copernicus_DSM_COG_10_N11_00_E106_00_DEM.tif` — 49,261,307 B (46.98 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (105.99986, 11.00014, 106.99986, 12.00014)
- `data/raw/copernicus_dem/Copernicus_DSM_COG_10_N15_00_E108_00_DEM.tif` — 32,885,605 B (31.36 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (107.99986, 15.00014, 108.99986, 16.00014)
- `data/raw/copernicus_dem/Copernicus_DSM_COG_10_N16_00_E108_00_DEM.tif` — 2,833,380 B (2.70 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (107.99986, 16.00014, 108.99986, 17.00014)

## data/raw/danang_portal

- Source URL: https://muangap.danang.gov.vn/
- Licence/access note: Government portal; reuse licence not stated in page/API response.

- `data/raw/danang_portal/167.6d7a7f50.chunk.js` — 923,574 B (0.88 MiB)
- `data/raw/danang_portal/742.f7fc329c.chunk.js` — 4,586,361 B (4.37 MiB)
- `data/raw/danang_portal/flood_reports.parquet` — 40,719 B (0.04 MiB)
  - 633 rows; columns/nulls (pre-2025 only; locked holdout excluded): id=0, lat=0, lon=0, datetime=0, depth_cm=0, address_road_text=0, status=410, flood_type=0, flood_unit=0
- `data/raw/danang_portal/homepage.html` — 3,192 B (0.00 MiB)
- `data/raw/danang_portal/main.3355aa3f.js` — 4,452 B (0.00 MiB)
- `data/raw/danang_portal/reports.json` — 601,576 B (0.57 MiB)
  - JSON records: 633; top-level keys: status, data
- `data/raw/danang_portal/resource_types.json` — 427 B (0.00 MiB)
  - JSON records: 2; top-level keys: status, total, data
- `data/raw/danang_portal/resources.json` — 252,803 B (0.24 MiB)
  - JSON records: 1353; top-level keys: status, total, data
- `data/raw/danang_portal/water_stations.json` — 31,374 B (0.03 MiB)
  - JSON records: 93

## data/raw/esa_worldcover

- Source URL: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/
- Licence/access note: ESA WorldCover 2021 v200, CC BY 4.0.

- `data/raw/esa_worldcover/ESA_WorldCover_10m_2021_v200_N09E105_Map.tif` — 92,338,709 B (88.06 MiB)
  - Raster 36000x36000; CRS EPSG:4326; bounds (105.0, 9.0, 108.0, 12.0)
- `data/raw/esa_worldcover/ESA_WorldCover_10m_2021_v200_N15E108_Map.tif` — 11,813,732 B (11.27 MiB)
  - Raster 36000x36000; CRS EPSG:4326; bounds (108.0, 15.0, 111.0, 18.0)

## data/raw/fabdem

- Source URL: https://huggingface.co/buckets/links-ads/fabdem/
- Licence/access note: FABDEM v1.2 hosting README states Non-Commercial Government Licence v2.0; non-commercial use.

- `data/raw/fabdem/N10E100-N20E110_FABDEM_V1-2/N10E106_FABDEM_V1-2.tif` — 22,066,596 B (21.04 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (105.99986, 10.00014, 106.99986, 11.00014)
- `data/raw/fabdem/N10E100-N20E110_FABDEM_V1-2/N11E106_FABDEM_V1-2.tif` — 32,722,659 B (31.21 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (105.99986, 11.00014, 106.99986, 12.00014)
- `data/raw/fabdem/N10E100-N20E110_FABDEM_V1-2/N15E108_FABDEM_V1-2.tif` — 25,997,807 B (24.79 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (107.99986, 15.00014, 108.99986, 16.00014)
- `data/raw/fabdem/N10E100-N20E110_FABDEM_V1-2/N16E108_FABDEM_V1-2.tif` — 2,306,952 B (2.20 MiB)
  - Raster 3600x3600; CRS EPSG:4326; bounds (107.99986, 16.00014, 108.99986, 17.00014)

## data/raw/ird_hcmc

- Source URL: https://dataverse.ird.fr/dataset.xhtml?persistentId=doi:10.23708/8Y16HU
- Licence/access note: CC BY 4.0 in ReadMe; Dataverse API says CC BY-NC 4.0 (conflict).

- `data/raw/ird_hcmc/Flood_event_locations.tab` — 96,977 B (0.09 MiB)
- `data/raw/ird_hcmc/HCMC_Floods_BDD.gpkg` — 249,856 B (0.24 MiB)
  - Layer Flood_event_locations: 425 rows; CRS EPSG:9210; columns/nulls (pre-2025 only; locked holdout excluded): Obs_id=0, Date=46, Year=0, Location_name=0, Location_type=0, District_mentioned=3, Ward=41, Current_admin_unit=5, Water_height_max_cm=244, Depth_class=0, Cause=0, Impact_type=0, Source_id=0, Source_type=0, Spatial_precision=0, Geocoding_method=0, Observation_notes=309, Commune=353, Province=372, Water_height_min_cm=281, Duration_hours=348
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

## data/raw/open_meteo

- Source URL: https://archive-api.open-meteo.com/v1/archive
- Licence/access note: Open-Meteo free historical API; attribution required, free tier non-commercial.

No files present.

## data/raw/open_meteo_invalid

- Source URL: https://archive-api.open-meteo.com/v1/archive
- Licence/access note: Quarantined ERA5-Land responses: API returned all-null precipitation/rain/showers; not valid rainfall data.

- `data/raw/open_meteo_invalid/era5_land_no_precip/10.55_106.45.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.55_106.55.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.55_106.65.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.55_106.75.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.55_106.85.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.55_106.95.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.65_106.45.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.65_106.55.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.65_106.65.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.65_106.75.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.65_106.85.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.65_106.95.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.75_106.45.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.75_106.55.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.75_106.65.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.75_106.75.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.75_106.85.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.75_106.95.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.85_106.45.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.85_106.55.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.85_106.65.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.85_106.75.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.85_106.85.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.85_106.95.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.95_106.45.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0
- `data/raw/open_meteo_invalid/era5_land_no_precip/10.95_106.55.parquet` — 1,770,045 B (1.69 MiB)
  - 217056 rows; time 2002-01-01 00:00:00 to 2026-10-05 23:00:00; columns/nulls: time=0, precipitation=217056, rain=217056, showers=217056, latitude_returned=0, longitude_returned=0, elevation_returned_m=0, requested_latitude=0, requested_longitude=0, model=0, nominal_grid_resolution=0

## data/raw/osm

- Source URL: https://www.openstreetmap.org/
- Licence/access note: OpenStreetMap ODbL 1.0; attribution required.

- `data/raw/osm/city_bboxes.json` — 1,123 B (0.00 MiB)
- `data/raw/osm/da_nang/admin_boundaries.gpkg` — 815,104 B (0.78 MiB)
  - Layer admin_boundaries: 399 rows; CRS EPSG:4326; columns/nulls: osm_id=0, name=0, admin_level=0, boundary=0, natural=399, other_tags=379
- `data/raw/osm/da_nang/roads.gpkg` — 9,625,600 B (9.18 MiB)
  - Layer roads: 29605 rows; CRS EPSG:4326; columns/nulls: osm_id=0, name=21184, highway=0, waterway=29605, other_tags=13064
- `data/raw/osm/da_nang/waterways_water.gpkg` — 774,144 B (0.74 MiB)
  - Layer waterways_water: 814 rows; CRS EPSG:4326; columns/nulls: osm_id=433, name=784, highway=814, waterway=444, other_tags=459, admin_level=814, boundary=814, natural=370
- `data/raw/osm/da_nang_boundary.json` — 233,334 B (0.22 MiB)
- `data/raw/osm/ho_chi_minh/admin_boundaries.gpkg` — 7,008,256 B (6.68 MiB)
  - Layer admin_boundaries: 3321 rows; CRS EPSG:4326; columns/nulls: osm_id=0, name=0, admin_level=0, boundary=0, natural=3321, other_tags=3124
- `data/raw/osm/ho_chi_minh/roads.gpkg` — 62,967,808 B (60.05 MiB)
  - Layer roads: 231548 rows; CRS EPSG:4326; columns/nulls: osm_id=0, name=170422, highway=0, waterway=231548, other_tags=152787
- `data/raw/osm/ho_chi_minh/waterways_water.gpkg` — 6,316,032 B (6.02 MiB)
  - Layer waterways_water: 5094 rows; CRS EPSG:4326; columns/nulls: osm_id=3223, name=4084, highway=5094, waterway=3325, other_tags=1851, admin_level=5094, boundary=5094, natural=1769
- `data/raw/osm/ho_chi_minh_boundary.json` — 638,759 B (0.61 MiB)
- `data/raw/osm/vietnam-latest.osm.pbf` — 329,770,361 B (314.49 MiB)

## data/raw/uhslc_vung_tau

- Source URL: https://uhslc.soest.hawaii.edu/data/?fd
- Licence/access note: UHSLC research-quality hourly sea level; source terms/attribution apply.

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
- Location precision categories in pre-2025 rows (`Spatial_precision`); whitespace trimmed; Hugh/Hgh normalized to High; locked holdout excluded:
  - Low: 219
  - Medium: 89
  - High: 67
- Location type categories in pre-2025 rows (`Location_type`):
  - Street: 276
  - Residential area: 29
  - Commune: 14
  - Ward: 9
  - National Highway: 9
  - Canal: 8
  - Intersection: 7
  - Neighborhood: 6
  - Bridge: 4
  - School: 3
  - Dike: 2
  - Market: 2
  - Tunnel: 1
  - Airport: 1
  - Provincial Road: 1
  - Parking: 1
  - Historical monument: 1
  - Roundabout: 1
- Geocoding method categories in pre-2025 rows (`Geocoding_method`):
  - Street point: 292
  - Area point: 69
  - Exact point: 9
  - Area_point: 3
  - Ward point: 1
  - Exact_point: 1
- Pre-2025 geometry types (geometry representation, not place type):
  - Point: 375
- Whole-street geometries in pre-2025 observation layer: 0; point geometries: 375.

## Da Nang reports

- Rows: 633; distinct dates 35; range 2022-10-14 12:00:00+07:00 to 2026-08-04 17:14:43+07:00; 2025–2026 rows 115 (count only; locked holdout).
- Rows per year (aggregate counts only):
  - 2022: 392
  - 2024: 126
  - 2025: 111
  - 2026: 4
- Rows on 2022-10-14: 392.
- Flood geometry type for pre-2025 rows:
  - street: 302
  - point: 216
- Depth availability pre-2025: 518 populated / 0 null.
- The page response has no dedicated cause or spatial-precision field; it provides point/street `flood_type`, coordinates, address text, water level, and status.

## OSM bbox extraction

- ho_chi_minh: roads=231548, waterways_water=5094, admin_boundaries=3321; admin levels present: 4, 6, 9.
- da_nang: roads=29605, waterways_water=814, admin_boundaries=399; admin levels present: 4, 6, 9.

## Design comparison

- IRD observations: design 425; observed 425 — match. Distinct dates: design 64; observed 64 — match. Undated rows: design 63; observed 63 — match.
- IRD cause counts (198 rain / 176 tide / 51 combined), depth-unknown count (257), and full-period precision distribution are design claims. Only pre-2025 attributes are reported above; these claims cannot be compared without inspecting the locked 2025–2026 holdout.
- IRD period: design says 2002–08/2026; aggregate rows exist in Year 2002–2026. Exact latest event date/month is intentionally not reported because the holdout is locked.
- Da Nang: design claims 633 reports, 35 dates, and 392 on 2022-10-14; compare the source-specific audit above against these claims.
- IRD license discrepancy: Dataverse API metadata says CC BY-NC 4.0; downloaded ReadMe says CC BY 4.0. Ask the authors before reuse.
- HCMC_Roads.gpkg is the IRD recurrence-by-street label layer (9 features), while HCMC_water.gpkg is rivers/canals/water-body geometry (2,430 features); road recurrence belongs only in label design, water geometry may supply spatial context.
- Open-Meteo ERA5-Land 0.1° provides no precipitation variables; initial all-null responses were quarantined. Rain acquisition must use precipitation-capable ERA5 at 0.25° and remains pending hourly quota reset. The API has not been called again after its quota stop.
- OSM requested admin levels were 4–10; observed levels in the OSM bbox extracts are reported above. Geofabrik fallback used GDAL OSM-driver bbox filtering because standalone osmium-tool CLI was unavailable; the country PBF itself was not loaded into a Python GeoDataFrame.

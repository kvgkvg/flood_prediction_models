# Routes and flood-label audit

Reproducible command: `PYTHONPATH=src .venv/bin/python scripts/make_routes_report.py` (bootstrap seed 713; 2,000 draws for rates, 600 for positive-route counts).

All label/matching summaries use train + train_undated records only. Both locked splits are shown only as per-city counts; distinct dates are counted only for test_locked rows with a date. Exact route totals are census counts of the cached OSM extract; uncertainty intervals are not meaningful for these finite totals.

## ho_chi_minh

- Routes: 140236 total (55371 named, 84865 unnamed; census).
- Ward boundary: finest available OSM admin level 9; 3151 polygons; 61.2% of bbox area covered (rest uses 1 km fallback cells).
- Routes by highway class: {'residential': 68115, 'service': 57201, 'tertiary': 4186, 'secondary': 2740, 'primary': 1924, 'primary_link': 1303, 'unclassified': 1303, 'trunk': 937, 'trunk_link': 784, 'secondary_link': 645, 'tertiary_link': 478, 'motorway': 284, 'motorway_link': 194, 'living_street': 142}.
- Length metres: median 77.7 (route-bootstrap 95% interval [77.1, 78.4]); IQR 34.2–194.5, mean 239.4.
- Eligible match rate: 365/375 = 97.3%, record-bootstrap 95% interval [95.5%, 98.9%]; types {'name+distance': 325, 'distance': 40, 'unmatched': 10}.
- Match by precision `area`: 62/70 (88.6%; bootstrap 95% interval [81.4%, 95.7%]).
- Match by precision `point`: 9/10 (90.0%; bootstrap 95% interval [70.0%, 100.0%]).
- Match by precision `street`: 294/295 (99.7%; bootstrap 95% interval [99.0%, 100.0%]).
- Match distance metres: median 3.2; IQR 1.4–6.4; p90 69.2; max 492.4.
- Unmatched examples (up to 15, eligible records only):
  - ird:Obs_86:86: Trường Mầm non Vành Khuyên
  - ird:Obs_97:97: Lái Thiêu
  - ird:Obs_136:136: Kênh Tẻ
  - ird:Obs_161:161: Xã Phong Phú
  - ird:Obs_163:163: Rạch Cây Điệp
  - ird:Obs_202:202: Phường Hiệp Bình Phước
  - ird:Obs_214:214: Khu B, Xã Bình Lợi
  - ird:Obs_216:216: Xã Tân Nhựt
  - ird:Obs_221:221: Rạch Mường Đình
  - ird:Obs_329:329: Cầu Ông Dầu
- Positive rain routes: 191/140236 (0.14%; route-bootstrap 95% interval [0.12%, 0.16%]); 13 positives outside modelling universe. Counts by highway class {'secondary': 70, 'primary': 43, 'residential': 30, 'tertiary': 29, 'service': 11, 'trunk': 7, 'trunk_link': 1}; positive-class shares (%) {'secondary': 36.6, 'primary': 22.5, 'residential': 15.7, 'tertiary': 15.2, 'service': 5.8, 'trunk': 3.7, 'trunk_link': 0.5}; all-route class shares (%) {'residential': 48.6, 'service': 40.8, 'tertiary': 3.0, 'secondary': 2.0, 'primary': 1.4, 'primary_link': 0.9, 'unclassified': 0.9, 'trunk': 0.7, 'trunk_link': 0.6, 'secondary_link': 0.5, 'tertiary_link': 0.3, 'motorway': 0.2, 'motorway_link': 0.1, 'living_street': 0.1}.
- Positive tide routes: 169/140236 (0.12%; route-bootstrap 95% interval [0.10%, 0.14%]); 18 positives outside modelling universe. Counts by highway class {'residential': 52, 'secondary': 40, 'tertiary': 28, 'primary': 25, 'service': 15, 'trunk': 5, 'unclassified': 4}; positive-class shares (%) {'residential': 30.8, 'secondary': 23.7, 'tertiary': 16.6, 'primary': 14.8, 'service': 8.9, 'trunk': 3.0, 'unclassified': 2.4}; all-route class shares (%) {'residential': 48.6, 'service': 40.8, 'tertiary': 3.0, 'secondary': 2.0, 'primary': 1.4, 'primary_link': 0.9, 'unclassified': 0.9, 'trunk': 0.7, 'trunk_link': 0.6, 'secondary_link': 0.5, 'tertiary_link': 0.3, 'motorway': 0.2, 'motorway_link': 0.1, 'living_street': 0.1}.
- Locked counts only: test_locked 33 records / 8 dates; test_locked_undated 17 records.

## da_nang

- Routes: 21429 total (8566 named, 12863 unnamed; census).
- Ward boundary: finest available OSM admin level 9; 380 polygons; 12.2% of bbox area covered (rest uses 1 km fallback cells).
- Routes by highway class: {'residential': 12011, 'service': 4876, 'unclassified': 1294, 'tertiary': 1090, 'secondary': 633, 'primary': 442, 'trunk': 241, 'primary_link': 219, 'living_street': 176, 'secondary_link': 172, 'trunk_link': 105, 'motorway': 95, 'tertiary_link': 49, 'motorway_link': 26}.
- Length metres: median 127.9 (route-bootstrap 95% interval [125.3, 130.8]); IQR 49.0–322.4, mean 334.6.
- Eligible match rate: 516/518 = 99.6%, record-bootstrap 95% interval [99.0%, 100.0%]; types {'name+distance': 433, 'distance': 83, 'unmatched': 2}.
- Match by precision `point`: 214/216 (99.1%; bootstrap 95% interval [97.7%, 100.0%]).
- Match by precision `street`: 302/302 (100.0%; bootstrap 95% interval [100.0%, 100.0%]).
- Match distance metres: median 7.4; IQR 2.3–14.0; p90 22.7; max 157.9.
- Unmatched examples (up to 15, eligible records only):
  - danang:64d5acf21f72f45e65079d10:608: Thôn Thạch Nham Tây, Xã Hòa Nhơn, Huyện Hòa Vang, 244R+FJ5, Hoà Nhơn, Hòa Vang, Đà Nẵng, Vietnam
  - danang:64d5ad021f72f45e65079d20:624: 24X3+FH5, Hoà Sơn, Hòa Vang, Đà Nẵng, Việt Nam
- Positive rain routes: 423/21429 (1.97%; route-bootstrap 95% interval [1.79%, 2.16%]); 28 positives outside modelling universe. Counts by highway class {'residential': 258, 'tertiary': 77, 'secondary': 27, 'service': 24, 'primary': 21, 'trunk': 10, 'unclassified': 4, 'living_street': 1, 'motorway': 1}; positive-class shares (%) {'residential': 61.0, 'tertiary': 18.2, 'secondary': 6.4, 'service': 5.7, 'primary': 5.0, 'trunk': 2.4, 'unclassified': 0.9, 'living_street': 0.2, 'motorway': 0.2}; all-route class shares (%) {'residential': 56.1, 'service': 22.8, 'unclassified': 6.0, 'tertiary': 5.1, 'secondary': 3.0, 'primary': 2.1, 'trunk': 1.1, 'primary_link': 1.0, 'living_street': 0.8, 'secondary_link': 0.8, 'trunk_link': 0.5, 'motorway': 0.4, 'tertiary_link': 0.2, 'motorway_link': 0.1}.
- Positive tide routes: 0/21429 (0.00%; route-bootstrap 95% interval [0.00%, 0.00%]); 0 positives outside modelling universe. Counts by highway class {}; positive-class shares (%) {}; all-route class shares (%) {'residential': 56.1, 'service': 22.8, 'unclassified': 6.0, 'tertiary': 5.1, 'secondary': 3.0, 'primary': 2.1, 'trunk': 1.1, 'primary_link': 1.0, 'living_street': 0.8, 'secondary_link': 0.8, 'trunk_link': 0.5, 'motorway': 0.4, 'tertiary_link': 0.2, 'motorway_link': 0.1}.
- 2022-10-14 concentration: 392 eligible records, 350 distinct matched routes, among 518 dated eligible records (75.7%).
- Locked counts only: test_locked 115 records / 18 dates; test_locked_undated 0 records.

## Assumptions

- Da Nang flood reports are classified as rain (`cause_assumed=True`). All source rows are treated as flood observations; non-locked records without dates are retained for route-level labels but do not contribute to date summaries.
- IRD cause text maps to rain/tide/combined by keyword; unmatched or empty values become unknown. Da Nang text is assumed to name a road when parsed from the first address segment.
- Location precision is inferred from source location type/geocoding method/precision fields; raw source values remain in the table. The hard HCMC bbox clamp is retained; source points are preserved without relocation or dropping.
- Named route fuzzy matching uses normalized sequence/token similarity >= 0.55; otherwise the nearest route within 40 m is used. Street/area records search named routes through 500 m.
- Unnamed route connectivity uses line intersections and a 2 m snapping tolerance in metric UTM; road-grade separation is not available in the OSM attributes used here. All reported counts are deterministic counts of these OSM downloads unless identified as bootstrap intervals.


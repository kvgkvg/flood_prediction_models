"""Fetch OSM administrative boundaries and save their 2 km buffered WGS84 bboxes."""
import json, time
from pathlib import Path
import requests
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
from floodrisk.cities import CITIES

OUT = Path('data/raw/osm')
NOMINATIM = 'https://nominatim.openstreetmap.org/search'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {}
    for slug, city in CITIES.items():
        dest = OUT / f'{slug}_boundary.json'
        if dest.exists():
            item = json.loads(dest.read_text())
        else:
            r = requests.get(NOMINATIM, params={'q': city.query_name, 'format':'jsonv2', 'polygon_geojson':1, 'limit':5}, headers={'User-Agent':'floodrisk-data-research/0.1 contact: data pipeline'}, timeout=60)
            r.raise_for_status()
            candidates = r.json()
            candidate = next((x for x in candidates if x.get('category')=='boundary' and x.get('type')=='administrative'), None)
            if candidate is None: raise RuntimeError(f'No OSM admin boundary found for {slug}')
            item = candidate
            dest.write_text(json.dumps(item))
            time.sleep(1.1)
        geom = shape(item['geojson'])
        project = Transformer.from_crs('EPSG:4326','EPSG:32648',always_xy=True).transform
        unproject = Transformer.from_crs('EPSG:32648','EPSG:4326',always_xy=True).transform
        buffered = transform(unproject, transform(project, geom).buffer(2000))
        result[slug] = {
            'bbox': list(city.bbox),
            'admin_bbox': list(city.admin_bbox),
            'osm_boundary_bbox_2km': list(buffered.bounds),
            'osm_type': item.get('osm_type'), 'osm_id': item.get('osm_id'),
            'display_name': item.get('display_name'),
            'urban_bbox_derivation': 'configured in src/floodrisk/cities.py',
            'admin_buffer_m': 2000,
        }
    (OUT/'city_bboxes.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False))
if __name__=='__main__': main()

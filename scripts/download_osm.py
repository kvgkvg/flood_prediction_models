#!/usr/bin/env python3
"""Fetch small urban OSM boxes by layer; cache exact Overpass JSON responses.

Overpass calls identify this client, print response bodies on failure, and back
off for 429/504. After exhausting three public mirrors, the script checks the
Geofabrik download speed before a resumable PBF download and bbox extract.
"""
from __future__ import annotations

import json
import argparse
import shutil
import subprocess
import time
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import LineString, MultiPolygon, Polygon, shape
from shapely import wkb as shapely_wkb
from shapely.ops import linemerge, polygonize, unary_union

from floodrisk.cities import CITIES

ROOT = Path("data/raw/osm")
USER_AGENT = "floodrisk-hackathon/0.1 (contact: team email unknown)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]
GEOFABRIK = "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf"


def _query(layer: str, bbox: tuple[float, float, float, float]) -> str:
    west, south, east, north = bbox
    area = f"{south},{west},{north},{east}"
    if layer == "roads":
        body = f'way["highway"]({area});'
    elif layer == "waterways_water":
        body = (f'way["waterway"~"^(river|canal|stream|drain)$"]({area});'
                f'way["natural"="water"]({area});'
                f'relation["natural"="water"]({area});')
    else:
        body = f'relation["boundary"="administrative"]["admin_level"~"^(4|5|6|7|8|9|10)$"]({area});'
    return f"[out:json][timeout:180];({body});out body geom;"


def _overpass(session: requests.Session, query: str) -> dict:
    errors = []
    for mirror in MIRRORS:
        for attempt in range(1):
            try:
                response = session.post(mirror, data={"data": query}, headers=HEADERS, timeout=90)
                if response.status_code == 200:
                    return response.json()
                detail = response.text[:2000]
                errors.append(f"{mirror} HTTP {response.status_code}: {detail}")
                if response.status_code in (403, 406) or "blocked" in detail.lower() or "captcha" in detail.lower():
                    raise RuntimeError("Overpass returned a block response; stop without trying other mirrors: " + errors[-1])
                if response.status_code in (429, 504):
                    time.sleep(10 * (attempt + 1))
                    continue
                break
            except requests.RequestException as exc:
                errors.append(f"{mirror} {type(exc).__name__}: {exc}")
                time.sleep(2 * (attempt + 1))
    raise ConnectionError("All three Overpass mirrors failed: " + "\n".join(errors))


def _relation_polygon(element: dict):
    outer, inner = [], []
    for member in element.get("members", []):
        coordinates = [(p["lon"], p["lat"]) for p in member.get("geometry", [])]
        if len(coordinates) >= 2:
            target = inner if member.get("role") == "inner" else outer
            target.append(LineString(coordinates))
    if not outer:
        return None
    shells = list(polygonize(linemerge(unary_union(outer))))
    holes = list(polygonize(linemerge(unary_union(inner)))) if inner else []
    polygons = []
    for shell in shells:
        contained = [h for h in holes if shell.contains(h.representative_point())]
        geom = shell.difference(unary_union(contained)) if contained else shell
        if not geom.is_empty:
            polygons.extend(list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom])
    return polygons[0] if len(polygons) == 1 else MultiPolygon(polygons) if polygons else None


def _to_gpkg(payload: dict, dest: Path, layer: str) -> list[int]:
    rows = []
    levels = set()
    for item in payload.get("elements", []):
        tags = item.get("tags", {})
        geom = None
        if item["type"] == "way":
            coords = [(p["lon"], p["lat"]) for p in item.get("geometry", [])]
            if len(coords) >= 2:
                if layer == "waterways_water" and tags.get("natural") == "water" and coords[0] == coords[-1]:
                    geom = Polygon(coords)
                else:
                    geom = LineString(coords)
        elif item["type"] == "relation":
            geom = _relation_polygon(item)
        if geom is None or geom.is_empty:
            continue
        levels.add(tags.get("admin_level"))
        rows.append({"osm_type": item["type"], "osm_id": item["id"],
                     "admin_level": tags.get("admin_level"), "highway": tags.get("highway"),
                     "waterway": tags.get("waterway"), "natural": tags.get("natural"),
                     "boundary": tags.get("boundary"), "name": tags.get("name"),
                     "tags": json.dumps(tags, ensure_ascii=False), "geometry": geom})
    dest.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326").drop_duplicates(["osm_type", "osm_id"])
        gdf.to_file(dest, layer=layer, driver="GPKG")
    return sorted(int(x) for x in levels if x and str(x).isdigit())


def _gdal_bbox_export(pbf: Path, city: str, bbox: tuple[float, float, float, float], outdir: Path):
    """Stream the country PBF through GDAL's OSM driver with a bbox filter.

    Used when the standalone osmium-tool executable is unavailable. The PBF is
    never materialized as a country-wide GeoDataFrame; GDAL applies its spatial
    filter while parsing and only bbox matches enter Python memory.
    """
    import pyogrio
    columns=['osm_id','name','highway','waterway','natural','boundary','admin_level','other_tags']
    pyogrio.set_gdal_config_options({'OSM_MAX_TMPFILE_SIZE':'128'})
    lines=pyogrio.read_dataframe(pbf,layer='lines',bbox=bbox,columns=columns,use_arrow=True)
    roads=lines.loc[lines['highway'].notna()].copy()
    water_lines=lines.loc[lines['waterway'].isin(['river','canal','stream','drain'])].copy()
    polys=pyogrio.read_dataframe(pbf,layer='multipolygons',bbox=bbox,columns=columns,use_arrow=True)
    water_polys=polys.loc[polys['natural'].eq('water')].copy()
    admin=polys.loc[polys['boundary'].eq('administrative') & polys['admin_level'].astype(str).isin({str(i) for i in range(4,11)})].copy()
    water=__import__('pandas').concat([water_lines,water_polys],ignore_index=True)
    for layer,gdf in [('roads',roads),('waterways_water',water),('admin_boundaries',admin)]:
        dest=outdir/f'{layer}.gpkg'; outdir.mkdir(parents=True,exist_ok=True)
        if dest.exists():
            print(f'cached {city}/{layer}',flush=True)
            continue
        if len(gdf):
            gdf.to_file(dest,layer=layer,driver='GPKG')
        else:
            gpd.GeoDataFrame({'osm_id':[]},geometry=gpd.GeoSeries([],crs='EPSG:4326'),crs='EPSG:4326').to_file(dest,layer=layer,driver='GPKG')
        levels=sorted(set(admin['admin_level'].dropna().astype(str))) if layer=='admin_boundaries' else []
        print(f'{city}/{layer}: {len(gdf)} features; admin_levels={levels}',flush=True)

def _fallback_pbf(session: requests.Session, city: str, bbox: tuple[float, float, float, float], outdir: Path):
    """Check size and a 2 MB range speed sample before resumable Geofabrik transfer."""
    head = session.head(GEOFABRIK, headers=HEADERS, allow_redirects=True, timeout=60)
    head.raise_for_status()
    total = int(head.headers.get("Content-Length", 0))
    if not total:
        raise RuntimeError(f"Geofabrik did not expose Content-Length: {head.url}")
    pbf = ROOT / "vietnam-latest.osm.pbf"
    pbf.parent.mkdir(parents=True, exist_ok=True)
    if pbf.exists() and pbf.stat().st_size == total:
        print(f"Geofabrik cached {head.url}; size={total} B; no redownload",flush=True)
    else:
        start = time.monotonic()
        sample = session.get(GEOFABRIK, headers={**HEADERS, "Range": "bytes=0-2097151"}, stream=True, timeout=60)
        sample.raise_for_status()
        received = sum(len(c) for c in sample.iter_content(256 * 1024) if c)
        sample.close()
        speed = received / max(time.monotonic() - start, 0.01)
        remaining=total-(pbf.stat().st_size if pbf.exists() else 0)
        eta = remaining / speed
        print(f"Geofabrik URL {head.url}; size={total}; sample={received}; speed={speed:.0f} B/s; remaining ETA={eta:.0f} s", flush=True)
    if not pbf.exists() or pbf.stat().st_size != total:
        offset = pbf.stat().st_size if pbf.exists() else 0
        with session.get(GEOFABRIK, headers={**HEADERS, "Range": f"bytes={offset}-"}, stream=True, allow_redirects=True, timeout=300) as r:
            if offset and r.status_code != 206:
                raise RuntimeError(f"Server ignored resume Range at {offset}, HTTP {r.status_code}")
            r.raise_for_status()
            with pbf.open("ab" if offset else "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        print(f"PBF bytes {f.tell()}/{total}", flush=True)
    if not shutil.which("osmium"):
        print('osmium-tool CLI not installed; using GDAL OSM PBF driver with pushed-down bbox filter.',flush=True)
        _gdal_bbox_export(pbf,city,bbox,outdir)
        return
    west, south, east, north = bbox
    extracted = outdir / f"{city}_extract.osm.pbf"
    subprocess.run(["osmium", "extract", "--bbox", f"{west},{south},{east},{north}", "--strategy=smart", str(pbf), "-o", str(extracted), "--overwrite"], check=True)
    # Convert only the bounded city extract, never the country PBF. Pyosmium's
    # node locations and area assembler operate on this small extract.
    import osmium
    factory=osmium.geom.WKBFactory()
    rows={name:[] for name in ('roads','waterways_water','admin_boundaries')}
    for obj in osmium.FileProcessor(str(extracted)).with_locations().with_areas():
        tags={t.k:t.v for t in obj.tags}
        geom=None; dest=None
        if isinstance(obj,osmium.osm.Way):
            if tags.get('highway'):
                try: geom=shapely_wkb.loads(factory.create_linestring(obj)); dest='roads'
                except Exception: pass
            if tags.get('waterway') in {'river','canal','stream','drain'}:
                try: geom=shapely_wkb.loads(factory.create_linestring(obj)); dest='waterways_water'
                except Exception: pass
        elif isinstance(obj,osmium.osm.Area):
            if tags.get('natural')=='water' or tags.get('waterway') in {'river','canal','stream','drain'}:
                try: geom=shapely_wkb.loads(factory.create_multipolygon(obj)); dest='waterways_water'
                except Exception: pass
            if tags.get('boundary')=='administrative' and tags.get('admin_level') in {str(i) for i in range(4,11)}:
                try: geom=shapely_wkb.loads(factory.create_multipolygon(obj)); dest='admin_boundaries'
                except Exception: pass
        if dest and geom is not None and not geom.is_empty:
            rows[dest].append({'osm_type':'area' if isinstance(obj,osmium.osm.Area) else 'way','osm_id':int(obj.id),
              'admin_level':tags.get('admin_level'),'highway':tags.get('highway'),'waterway':tags.get('waterway'),
              'natural':tags.get('natural'),'boundary':tags.get('boundary'),'name':tags.get('name'),
              'tags':json.dumps(tags,ensure_ascii=False),'geometry':geom})
    for layer,items in rows.items():
        if items:
            gpd.GeoDataFrame(items,geometry='geometry',crs='EPSG:4326').drop_duplicates(['osm_type','osm_id']).to_file(outdir/f'{layer}.gpkg',layer=layer,driver='GPKG')
        print(f'{city}/{layer}: bounded PBF features={len(items)}',flush=True)



def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--resume-geofabrik',action='store_true',help='skip Overpass and resume the cached Geofabrik PBF transfer/extract')
    args=parser.parse_args()
    session = requests.Session()
    for slug, city in CITIES.items():
        outdir = ROOT / slug
        if args.resume_geofabrik:
            expected=[outdir/f'{layer}.gpkg' for layer in ('roads','waterways_water','admin_boundaries')]
            if all(p.exists() for p in expected):
                print(f'cached {slug} OSM layers; PBF remains at {ROOT / "vietnam-latest.osm.pbf"}',flush=True)
                continue
            _fallback_pbf(session,slug,city.bbox,outdir)
            continue
        for layer in ("roads", "waterways_water", "admin_boundaries"):
            raw = outdir / f"{layer}.json"
            gpkg = outdir / f"{layer}.gpkg"
            if gpkg.exists():
                print(f"cached {slug}/{layer}", flush=True)
                continue
            if raw.exists():
                payload = json.loads(raw.read_text())
            else:
                try:
                    payload = _overpass(session, _query(layer, city.bbox))
                except ConnectionError:
                    _fallback_pbf(session, slug, city.bbox, outdir)
                    raise
                raw.parent.mkdir(parents=True, exist_ok=True)
                raw.write_text(json.dumps(payload))
            levels = _to_gpkg(payload, gpkg, layer)
            count = len(payload.get("elements", []))
            print(f"{slug}/{layer}: elements={count}, admin_levels={levels}", flush=True)
            time.sleep(1.0)


if __name__ == "__main__":
    main()

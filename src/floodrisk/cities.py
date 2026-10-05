"""City definitions and OSM-boundary-derived buffered bounding boxes (WGS84)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class City:
    slug: str
    query_name: str
    # Filled by scripts/fetch_city_bboxes.py from the OSM admin boundary.
    bbox: tuple[float, float, float, float] | None = None  # west, south, east, north

CITIES = {
    # Current OSM administrative boundaries (queried 2026-10-06), buffered 2 km.
    # The current Ho Chi Minh City and Da Nang relations include the post-2025
    # administrative expansions; flood observations remain concentrated in the
    # former urban footprints, so acquisition coverage and event coverage differ.
    "ho_chi_minh": City("ho_chi_minh", "Thành phố Hồ Chí Minh, Vietnam", (105.9587613435, 8.3276167976, 108.4493015074, 11.5196700168)),
    "da_nang": City("da_nang", "Đà Nẵng, Vietnam", (107.1922534859, 14.9332972088, 109.0421847443, 16.3520559807)),
}

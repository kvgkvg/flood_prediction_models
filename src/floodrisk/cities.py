"""Urban acquisition areas and retained OSM administrative reference boxes (WGS84)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class City:
    slug: str
    query_name: str
    bbox: tuple[float, float, float, float]  # west, south, east, north; urban working area
    admin_bbox: tuple[float, float, float, float]  # previous 2 km OSM admin-boundary box

CITIES = {
    "ho_chi_minh": City(
        "ho_chi_minh", "Thành phố Hồ Chí Minh, Vietnam",
        (106.4363502282, 10.55, 107.0, 11.05),
        (105.9587613435, 8.3276167976, 108.4493015074, 11.5196700168),
    ),
    "da_nang": City(
        "da_nang", "Đà Nẵng, Vietnam",
        (108.05, 15.93, 108.35, 16.16),
        (107.1922534859, 14.9332972088, 109.0421847443, 16.3520559807),
    ),
}

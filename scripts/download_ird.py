#!/usr/bin/env python3
"""Download every publicly accessible file of IRD Dataverse DOI 10.23708/8Y16HU."""
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://dataverse.ird.fr/api"
DOI = "doi:10.23708/8Y16HU"
OUT = Path("data/raw/ird_hcmc")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    meta = s.get(f"{API}/datasets/:persistentId/", params={"persistentId": DOI}, timeout=60)
    meta.raise_for_status()
    payload = meta.json()["data"]
    (OUT / "dataverse_metadata.json").write_text(meta.text)
    files = payload["latestVersion"]["files"]
    for item in files:
        data = item["dataFile"]
        name = Path(data["filename"]).name
        dest = OUT / name
        if dest.exists() and dest.stat().st_size >= data.get("filesize", -1):
            print(f"cached {name}")
            continue
        url = f"{API}/access/datafile/{data['id']}"
        tmp = dest.with_suffix(dest.suffix + ".part")
        with s.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
            if data.get("filesize") and tmp.stat().st_size < data["filesize"]:
                raise IOError(f"size mismatch for {name}: {tmp.stat().st_size} != {data['filesize']}")
            tmp.replace(dest)
        print(f"downloaded {name} {dest.stat().st_size}")

if __name__ == "__main__":
    main()

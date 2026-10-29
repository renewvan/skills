#!/usr/bin/env python3
"""Helpers for the build-basemap skill.

  basemap.py bbox "<place>"          place name -> MIN_LON,MIN_LAT,MAX_LON,MAX_LAT (Nominatim)
  basemap.py bbox "<place>" --geojson FILE
                                     also write the place outline for `pmtiles extract --region`
  basemap.py tile LAT LON [--zoom Z] z/x/y of the tile under a point, for `pmtiles tile`

Nominatim returns [south, north, west, east]; pmtiles wants west,south,east,north. The
reordering is the one thing here that is easy to get wrong by hand, hence the script.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.parse
import urllib.request

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "renewvan-build-basemap/0.1 (github@renewvan.com)"


def nominatim_to_bbox(boundingbox: list[str]) -> str:
    """Nominatim [south, north, west, east] -> pmtiles MIN_LON,MIN_LAT,MAX_LON,MAX_LAT."""
    south, north, west, east = (float(v) for v in boundingbox)
    if not (-90 <= south < north <= 90 and -180 <= west <= 180 and -180 <= east <= 180):
        raise ValueError(f"implausible bounding box: {boundingbox}")
    if west >= east:
        raise ValueError(f"bounding box crosses the antimeridian, split it by hand: {boundingbox}")
    return f"{west:.4f},{south:.4f},{east:.4f},{north:.4f}"


def tile_for(lat: float, lon: float, zoom: int = 14) -> tuple[int, int, int]:
    if not (-85.0511 <= lat <= 85.0511 and -180 <= lon <= 180):
        raise ValueError(f"lat/lon out of range: {lat}, {lon}")
    n = 2**zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return zoom, min(x, n - 1), min(y, n - 1)


def lookup(place: str, with_polygon: bool) -> dict:
    params = {"q": place, "format": "jsonv2", "limit": "1"}
    if with_polygon:
        params["polygon_geojson"] = "1"
    req = urllib.request.Request(
        f"{NOMINATIM}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        results = json.load(resp)
    if not results:
        raise LookupError(f"no match for {place!r}")
    return results[0]


def cmd_bbox(args: argparse.Namespace) -> int:
    hit = lookup(args.place, with_polygon=bool(args.geojson))
    print(f"# {hit['display_name']} ({hit.get('type')})", file=sys.stderr)
    print(nominatim_to_bbox(hit["boundingbox"]))
    if args.geojson:
        feature = {"type": "Feature", "properties": {}, "geometry": hit["geojson"]}
        with open(args.geojson, "w") as fh:
            json.dump(feature, fh)
        print(f"# outline written to {args.geojson}", file=sys.stderr)
    return 0


def cmd_tile(args: argparse.Namespace) -> int:
    z, x, y = tile_for(args.lat, args.lon, args.zoom)
    print(z, x, y)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_bbox = sub.add_parser("bbox", help="resolve a place name to a bounding box")
    p_bbox.add_argument("place")
    p_bbox.add_argument("--geojson", metavar="FILE", help="write the place outline here")
    p_bbox.set_defaults(func=cmd_bbox)

    p_tile = sub.add_parser("tile", help="z/x/y of the tile under a point")
    p_tile.add_argument("lat", type=float)
    p_tile.add_argument("lon", type=float)
    p_tile.add_argument("--zoom", type=int, default=14)
    p_tile.set_defaults(func=cmd_tile)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, LookupError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

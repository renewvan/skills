---
name: build-basemap
description: Build the offline PMTiles basemap (public/maps/basemap.pmtiles) for the renewvan dashboard from a region, city or country name, verify it covers a given point, and optionally push it to the Pi. Use when the user wants to make, rebuild, resize or change the area of the dashboard's offline map, or the Map page is empty or shows "Offline map unavailable".
license: MIT
metadata:
  version: "1.1.0"
  domain: renewvan
argument-hint: "[place]"
allowed-tools: Bash, Read
---

# Build the offline basemap

Makes the one `basemap.pmtiles` file the dashboard's Map page reads, for a place the user
names. The source of truth is `dashboard/docs/offline-map.md` (and
`docs/adr/0001-self-hosted-pmtiles-basemap.md`): read it if anything below disagrees with the
repo. This skill covers the default route, `pmtiles extract` (section 1 of that doc). It does
not cover the self-build from OpenStreetMap: that route is untested end to end; point the user
at section 2 of the doc if they ask for it.

## Step 1 — Collect inputs

Ask only for what you cannot infer:

- **Place**: region, city or country name (`Portugal`, `Hastings`, `Baden-Württemberg`).
- **A point they will be at** (lat/lon) for the final check. Default: the place's centre.
- **Dashboard checkout**: default `../dashboard` next to this repo, or the cwd if it is the
  dashboard. The output is always `<dashboard>/public/maps/basemap.pmtiles` (git-ignored),
  whatever the route. That one path is what `vp dev` and Demo mode serve locally **and** what
  gets pushed to the Pi, so the file is built once, checked on localhost, then copied. Never
  write it elsewhere and copy it in later. `public/maps/` already holds the fonts and sprites:
  confirm it exists (a wrong checkout otherwise creates a stray tree).
- **Push to the Pi?** Default no. Needs the hub checkout and an ssh alias.

Check `pmtiles version` works. If not, tell the user to install the
[pmtiles CLI](https://docs.protomaps.com/pmtiles/cli) and stop.

## Step 2 — Resolve the area

```bash
python3 scripts/basemap.py bbox "<place>" [--geojson outline.geojson]
```

Resolve `scripts/basemap.py` against this skill's own directory, not the dashboard. It asks
OpenStreetMap's Nominatim (one request, with a User-Agent) and prints
`MIN_LON,MIN_LAT,MAX_LON,MAX_LAT` on stdout, the place it matched on stderr. **Show the matched
name to the user** and confirm it is the place they meant: Nominatim takes the first hit, and
names like `Georgia` or `Valencia` are ambiguous. Rerun with a more specific query if not.

- A bounding box takes in sea and neighbouring land. For a **country**, pass `--geojson` and use
  `--region=outline.geojson` instead of `--bbox`: the doc measured Spain at 1.7 GB by box
  against about 1.1 GB by outline, and Norway 4.1 GB against about 1.6 GB.
- A box that crosses the antimeridian is rejected: split it by hand.

## Step 3 — Pick a build and size it

The style needs a **version 4** Protomaps build. Daily builds are listed at
<https://maps.protomaps.com/builds>; pick the latest `YYYYMMDD`, and ask the user to confirm it
if the page cannot be read. Protomaps asks that its downloads are not hotlinked, so run the
extract once and keep the file.

Always dry-run first. It reads only the build's directories (a few MB), prints what the real
run would transfer and write, and creates nothing:

```bash
pmtiles extract https://build.protomaps.com/YYYYMMDD.pmtiles public/maps/basemap.pmtiles \
  --bbox=MIN_LON,MIN_LAT,MAX_LON,MAX_LAT --maxzoom=14 --dry-run
```

Report the size to the user and get a go-ahead before the real run. Reference sizes at
`--maxzoom=14`: Hastings-sized area 8 MB, Portugal 344 MB, UK 1.5 GB, Spain 1.7 GB, Norway
4.1 GB. Each extra zoom level roughly doubles it; keep `--maxzoom=14` (what the dashboard
matches) unless the user asks otherwise. The Pi's free disk must hold the file: if the Pi push
is wanted, check that before a multi-GB download.

## Step 4 — Extract

Run from the dashboard checkout (`cd <dashboard>` first: the output path is relative), the
same command without `--dry-run`. Any other route writes to the same path: a map built with
Planetiler uses `--output=public/maps/basemap.pmtiles`. If `basemap.pmtiles`
already exists, tell the user it will be replaced and confirm first.

## Step 5 — Verify

```bash
pmtiles verify public/maps/basemap.pmtiles
pmtiles show public/maps/basemap.pmtiles
python3 scripts/basemap.py tile <LAT> <LON>          # prints: 14 X Y
pmtiles tile public/maps/basemap.pmtiles 14 X Y | wc -c
```

Done only when all of these hold:

1. `verify` and `show` exit 0 (exit 1 means a killed or truncated file: delete it and rerun).
2. The `version` line in `show` starts with `4.` (not the `pmtiles spec version: 3` line).
3. The tile byte count under the user's point is **> 0**. Bounds are what was asked for, not
   proof tiles exist there; a 0 means the map will be blank at that spot.

State the result per check, and say plainly if one was not run.

## Step 6 — Check on localhost, then copy to the Pi

Do the localhost check first; push only once it looks right.

- **`vp dev` / Demo mode**: nothing more. They read `public/maps/basemap.pmtiles`. Demo mode
  drives in downtown Freiburg (47.9955 N 7.8529 E), so it only shows streets if the file
  covers Freiburg. After a reload the map can be blank (Vite's `no-cache` makes the range
  reads return `304`): hard-reload or tick "Disable cache".
- **The Pi**, only if asked, copying that same file from the hub checkout:

  ```bash
  scripts/push-basemap.sh ../dashboard/public/maps/basemap.pmtiles [--host <ssh-alias>]
  ```

  It verifies, swaps the file safely and restarts the container. The path, `.env` key and
  mount are the hub's side (hub README): do not copy them. Then check the Pi serves it:
  `curl -sI -H 'Range: bytes=0-16383' http://<hub>/maps/basemap.pmtiles` must be `206`, and
  open the Map page with a GPS fix inside the area: that is the check that matters.

## Do not

- Do not follow `main` or a non-4.x build blindly: the dashboard's style (`@protomaps/basemaps`
  5.x) renders tileset major 4 only.
- Do not commit the file (`*.pmtiles` is git-ignored) or mount the `maps/` directory (it hides
  the fonts and sprites; mount the single file).
- Do not share the file without credit: OpenStreetMap contributors (ODbL), ESA WorldCover
  (CC-BY 4.0). See "Redistributing a basemap" in the doc.

## Claude Code notes

Invoke as `/build-basemap`. `scripts/basemap.py` resolves against the
`[Skill directory: …]` footer Claude Code appends when this skill loads.

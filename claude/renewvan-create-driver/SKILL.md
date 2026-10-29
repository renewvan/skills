---
name: renewvan-create-driver
description: Bootstrap a new renewvan/driver-<entity> repo (MQTT skeleton, layered config, systemd unit, Dockerfile, CI) from the driver-tank reference shape, then run a design round for its topics and hardware interface. Use when the user wants to scaffold a new renewvan device, create driver-<entity>, or start integrating a new device into the renewvan hub.
license: MIT
metadata:
  version: "3.0.0"
  domain: renewvan
argument-hint: "[entity-slug]"
---

# Scaffold a renewvan device

Generates a new `driver-<entity>` repo in the shape `renewvan/driver-tank`'s
README documents as the reference for every `driver-*` repo: a pure-function
core, a layered `config.default.ini`/`config.ini` loader, a persistent MQTT
publisher with LWT that publishes retained Driver info (from `manifest.json`
plus the `DRIVER_VERSION` build arg) before `online`, a thin publish loop, a
systemd unit, and its own Dockerfile + CI (tests, manifest gate, release).
Contract: `hub/docs/authoring-a-driver.md`. This skill bootstraps that skeleton only —
`driver.py`'s read-publish step ships as a deliberate `NotImplementedError`.
Design and implementation are Step 5, not this skill's job to finish.

## Step 1 — Collect scaffold inputs

Ask the user directly (these are mechanical inputs, not open design
decisions):

- **Entity slug**: lowercase, `[a-z][a-z0-9_]*` (e.g. `gps`). Becomes the
  entity topic segment (`renewvan/gps/...`), the Python package (`driver_gps`),
  the repo name (`driver-gps`) and the Driver key (`gps`, the repo name minus
  `driver-`: manifest `driver`, `renewvan/<key>/info` and `/health`).
- **One-line description** for `pyproject.toml`/README/GitHub repo
  description. Must not contain `"`, `\` or newlines (they land in TOML/INI
  files; the script rejects them).
- **Target directory**. Default: a `driver-<entity>` sibling next to whichever
  `renewvan/*` repo the agent is currently in (e.g. `../driver-gps` next to
  `hub`) — ask only if that default is ambiguous.
- **Publish to GitHub?** If yes, needs `gh` authenticated against the
  `renewvan` org (`gh auth status`); if no org access, scaffold locally only
  and say so.

## Step 2 — Generate

```
python3 scripts/scaffold.py <entity-slug> "<Entity Title>" "<description>" <target-dir>
```

Resolve `scripts/scaffold.py` against this skill's own directory (the directory
this `SKILL.md` was loaded from), not the target repo. The
script copies `templates/driver-skeleton/`, substitutes
`__ENTITY__`/`__ENTITY_TITLE__`/`__PACKAGE__`/`__REPO__`/`__DESCRIPTION__`/
`__YEAR__` in every path and file, renames the package directory, and strips
`.tmpl` suffixes — it is deterministic; don't hand-copy or retype any
template file yourself. Refuses to run over an existing target directory
and rejects a malformed entity slug. It removes the target if generation
fails midway, checks that no `__TOKEN__` placeholder survives, and prints
`REPO=… PACKAGE=…` on its last line: **use that repo name below, not
`driver-<entity>`** — underscores in the slug become hyphens in the repo name
(`gps_fix` → `driver-gps-fix`) but stay underscores in the package.

## Step 3 — Commit and publish

```
cd <target-dir> && git init -b main && git add -A && git commit -m "Scaffold <repo> from the driver-tank reference shape"
```

If GitHub was requested:

```
gh repo create renewvan/<repo> --public --source=. --remote=origin --push
```

## Step 4 — Smoke-verify

```
cd <target-dir> && python3 -m venv .venv && . .venv/bin/activate \
  && pip install -r requirements.txt -r requirements-test.txt && pytest tests/ -v
```

(A venv keeps the install out of the user's global Python; the skeleton's
`.gitignore` already covers `.venv/`.)

Must pass out of the box (defaults only, no hardware/broker needed) — the
scaffolded tests exercise `config.py`'s layered loader and the Driver info
payload (`driver_info.py`). A failure here
means the scaffold itself is broken, not the (intentionally unimplemented)
driver.

## Step 5 — Hand off to design

The repo is a shell, not a device yet: `driver.py`'s `read_and_publish()`
raises `NotImplementedError`, and `config.py`'s `DeviceConfig` has no
hardware-specific fields. Tell the user this plainly, then run this fixed
design round (same question-then-wait shape as the `grilling` skill, scoped
to exactly these five questions — don't open-end it into a full grilling
session unless the user asks for one):

```
❓ Q1 - Sensing or remapping?: Does this device own the sensing (reads a
physical sensor/bus directly, like driver-tank's ADS1115) or remap an
existing feed (subscribes to a vendor's own MQTT/API and republishes, like
driver-venus's Victron remap)? This decides driver.py's shape.

❓ Q2 - Published fields: What properties does renewvan/<entity>/<id>/
<property> publish, and which are identity (published once) vs live
(republished every poll)? See driver-tank README's "Topics published"
section for the split.

❓ Q3 - New hub schema entity, or does this extend one of tank/relay/
battery/router? If new, it needs hub/schema/<entity>.schema.json + example
fixtures (hub/schema/validate-examples.sh must pass) + a demo scenario
(Step 6).

❓ Q4 - Hardware interface: what config keys does DeviceConfig need (serial
port, I2C address, remote host, baud rate, polling interval)? These go in
both config.py's DeviceConfig dataclass and config.default.ini.

❓ Q5 - Hub integration: once a version is tagged and
ghcr.io/renewvan/driver-<entity>:<tag> is published, does
hub/docker-compose.yml need a new service block (pattern: driver-tank's
block) and hub/.env.example keys? Not yet — only once a real image exists.
```

Wait for answers before writing any implementation code. Once settled, fill
`manifest.json`'s `source` and `publishes` (the manifest must validate
against `hub/schema/driver-manifest.schema.json`; a new entity must first be
added to the `publishes` enum in both the manifest and info schemas, see
"When you add an entity" in `hub/docs/authoring-a-driver.md`), update `CONTEXT.md` (the field glossary) and the README's "Topics
published"/"Wiring" sections to match — they currently carry `TODO`
markers, not placeholders to leave in place.

## Step 6 — Done criteria (hub side)

Follow the hub's `AGENTS.md`: run `./schema/validate-examples.sh` after any
schema change, and `python3 schema/validate-demo.py` (needs
`pip install jsonschema`) when an entity gains a schema or a required
property. Do not add a Dockerfile or local build to the hub: services ship as
pinned images.

- **New entity**: not done until `hub/schema/<entity>.schema.json`, example
  fixtures and `hub/schema/demo/<entity>.demo.json` exist and both validators
  pass. Scenario format and what it must exercise (optional-absent case,
  alarm/fault step): `hub/docs/demo-mode.md`.
- **Existing entity**: no demo, and `hub/schema/demo/` stays untouched; the
  Driver only complies with the entity schema (`hub/docs/porting-dbus-to-mqtt-driver.md`,
  "Adding a driver for an existing entity").
- **Demo fleet**: add the Driver to `hub/schema/demo/fleet.demo-fleet.json` in
  the same change as its first release if Demo mode should show it.
- **Porting a Venus OS D-Bus package** (`dbus-ads1115`, `dbus_wattcycle_ble`,
  `dbus-autoterm`, `dbus-giandel-bridge`): follow the recipe in
  `hub/docs/porting-dbus-to-mqtt-driver.md` alongside the design round. Suggest
  the `tdd` skill for the sensing logic, `diagnosing-bugs` for failures and
  `code-review` before merging.
- **Shipping**: once an image is released, pin its tag in the hub's
  `docker-compose.yml` `image:` line (the single source of truth, not `.env`),
  then hand off to the hub's `/renewvan-deploy` skill.

## Claude Code notes

Invoke as `/create-driver`. `scripts/scaffold.py` resolves against the
`[Skill directory: …]` footer Claude Code appends when this skill loads. For
Step 5's design round you may use the `grilling` skill's question format
directly, limited to the five questions listed. For Step 6, the `tdd`,
`diagnosing-bugs` and `code-review` skills fit the porting flow; when the
user is porting a `dbus-*` package, hand off to `/port-dbus-driver`.

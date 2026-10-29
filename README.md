# renewvan/skills

Installable agent skills for the **renewvan** ecosystem (see `renewvan/hub`'s
`CONTEXT.md` for domain vocabulary). Five skills: `create-driver`, `port-dbus-driver`, `flash-esp32`, `build-basemap` and `deploy`.

## Variants and versions

Every skill ships in two variants with the same name and the same
`metadata.version` (semver, bumped when the skill's behaviour changes):

| Variant | Where | For |
| ------- | ----- | --- |
| **General** | `skills/<name>/` | Any harness that reads `.agents/skills/` (Codex, Cursor, OpenCode, …). Harness-neutral wording, standard frontmatter only. The source of truth. |
| **Claude Code** | `claude/<name>/` | Claude Code (`.claude/skills/`). The same skill plus `allowed-tools`/`argument-hint` frontmatter and a "Claude Code notes" section (slash-command names, chaining other skills). **Generated, do not edit.** |

Edit `skills/<name>/` (and `claude-overrides/<name>.md` for Claude-only
additions), then rebuild:

```bash
python3 scripts/build_claude.py
```

`tests/test_skills.py` fails if `claude/` is stale or the versions differ.

## Install

Pick the variant for your harness and copy the skill directories (one level
under the skills root, non-recursive). Use a project-local root instead of the
user-wide one to scope a skill to one checkout.

```bash
git clone git@github.com:renewvan/skills.git /tmp/renewvan-skills

# General (.agents/skills)
mkdir -p ~/.agents/skills
cp -R /tmp/renewvan-skills/skills/* ~/.agents/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R /tmp/renewvan-skills/claude/* ~/.claude/skills/
```

**Via a GitHub-source skill installer** (same shape as installing
`mattpocock/skills` or `vercel-labs/skills`): point it at `renewvan/skills`,
skill path `skills/<name>/SKILL.md` (general) or `claude/<name>/SKILL.md`.

`renewvan/hub` ships its own copy of `deploy` under `.agents/skills/deploy`
(symlinked into `.claude/skills`), so you only need to install it here when
working outside the hub checkout (it still needs a hub checkout to run).

## Skills

| Skill | Version | Use it to |
| ----- | ------- | --------- |
| `create-driver` | 2.0.0 | Bootstrap a new `driver-<entity>` repo and run its design round |
| `port-dbus-driver` | 1.0.0 | Port a Venus OS D-Bus package to a native MQTT driver |
| `flash-esp32` | 1.0.0 | Build and flash an ESP32 firmware variant, then verify it on the bus |
| `build-basemap` | 1.1.0 | Build the dashboard's offline PMTiles basemap |
| `deploy` | 1.0.0 | Deploy the hub to the Pi |

How they fit together is in `renewvan/hub`'s `docs/agent-skills.md`.

### `deploy`

Deploys the hub to a Raspberry Pi with `bin/deploy.sh` (rsync, venvs, systemd
services, `docker compose pull && up -d`). Run it from the `renewvan/hub`
checkout: it stops with a clone hint if `bin/deploy.sh` is not found, rather
than improvising, and points at `bin/bootstrap-pi.sh` for a brand-new Pi. It checks the Pi is reachable (`ssh renewvan exit`, alias
overridable with `--host`) and warns about uncommitted changes (the script
rsyncs the working tree), runs the deploy, verifies with `docker compose ps`
and logs for any service that is not `running`, and explains the two cases the
script does not handle on its own: systemd plugin services (`renewvan-kiosk`,
`renewvan-tailscale`) that must be restarted by hand after a `.service`
change, and the optional GPS profile. A table maps common failures (rsync
permissions, missing `.env`, missing `tank/config.ini`, SSH drops) to fixes.
The script is idempotent: re-run it after a failure.

See `skills/deploy/SKILL.md` for the full process.

### `flash-esp32`

Flashes a renewvan ESP32 board from the `renewvan/driver-esp32` checkout by
driving its `scripts/flash.sh` (which stamps the version from `git describe`
and merges the variant's manifest). The script is deliberately **not** copied
here: it depends on the checkout's `manifests/`, `firmware/`, `packages/` and
git history, and a copy would drift. The skill instead asks for what is
missing: the variant, USB first flash vs OTA update, the serial port, and the
`secrets.yaml` values (WiFi, broker, OTA password, API key; it never prints or
commits them). It checks `esphome` and the layout, warns about `-dirty`
versions, the relay board's `OE` pull-up and the one-board-per-van limit, then
verifies the retained state, info and health topics on the bus.

See `skills/flash-esp32/SKILL.md` for the full process.

### `port-dbus-driver`

Turns a Venus OS D-Bus package (`dbus-ads1115`, `dbus_wattcycle_ble`,
`dbus-autoterm`, `dbus-giandel-bridge`) into a native MQTT driver by following
the hub's `docs/porting-dbus-to-mqtt-driver.md`. It does not scaffold or
implement on its own: it inventories the package into strip / keep / add, gets
the user's go-ahead, then sequences the work: settle entity and topics,
`create-driver`, test-first port of the sensing logic, manifest and Driver
info, hub schema + demo scenario + both validators when the entity is new,
diagnose, review, and finally pin the image in the hub's compose file and hand
off to `deploy`. Genuine Victron gear is out of scope (that is `driver-venus`'s
remap shape).

See `skills/port-dbus-driver/SKILL.md` for the full process.

### `create-driver`

Bootstraps a new `renewvan/driver-<entity>` repo: MQTT publisher skeleton,
layered `config.default.ini`/`config.ini` loader, `manifest.json` + retained
Driver info, systemd unit, Dockerfile, CI (tests, manifest gate, release) — the same shape `driver-tank`'s README documents as the reference for
every `driver-*` repo. Scaffolds only; it deliberately does not implement the
device's sensing/publishing logic, and ends by running a fixed design round
(sensing-vs-remapping, published fields, hub schema, hardware config, hub
integration) so a real device still gets designed, not left half-built.

See `skills/create-driver/SKILL.md` for the full process.

### `build-basemap`

Builds the dashboard's offline `basemap.pmtiles` for a region, city or country
by name: resolves the area to a bounding box (or outline) via Nominatim, picks
a Protomaps v4 build, dry-runs `pmtiles extract` to size it, extracts,
verifies the file (including that tiles exist under a given point), and
optionally pushes it to the Pi with the hub's script. Follows
`renewvan/dashboard`'s `docs/offline-map.md`; the self-build from OpenStreetMap
route is out of scope.

See `skills/build-basemap/SKILL.md` for the full process.

## Development

`scripts/build_claude.py` generates `claude/` from `skills/` (see
"Variants and versions"); commit both.

`skills/create-driver/scripts/scaffold.py` is the one piece of real code
here — everything else is markdown/templates. `tests/test_scaffold.py`
exercises it end to end (scaffolds into a temp dir, asserts the layout and
token substitution). Run before opening a PR:

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

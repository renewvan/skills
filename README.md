# renewvan/skills

Installable agent skills for the **renewvan** ecosystem (see `renewvan/hub`'s
`CONTEXT.md` for domain vocabulary). Four skills: `renewvan-create-driver`, `renewvan-flash-esp32`, `renewvan-build-basemap` and `renewvan-deploy`.

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

`renewvan-deploy` can be installed anywhere, but it only runs against a
`renewvan/hub` checkout (it verifies this in Step 0). The hub does not ship its
own copy; to use the skills inside the hub checkout, symlink them from a clone
of this repo so they never drift:

```bash
ln -s <clone>/skills/renewvan-* <hub>/.agents/skills/
```

## Skills

| Skill | Version | Use it to |
| ----- | ------- | --------- |
| `renewvan-create-driver` | 3.2.0 | Bootstrap a new `driver-<entity>` repo and run its design round |
| `renewvan-flash-esp32` | 4.0.0 | Build and flash an ESP32 firmware variant, then verify it on the bus |
| `renewvan-build-basemap` | 2.0.0 | Build the dashboard's offline PMTiles basemap |
| `renewvan-deploy` | 2.0.1 | Deploy the hub to the Pi |

How they fit together is in `renewvan/hub`'s `docs/agent-skills.md`.

### `renewvan-deploy`

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

See `skills/renewvan-deploy/SKILL.md` for the full process.

### `renewvan-flash-esp32`

Flashes a renewvan ESP32 board from the `renewvan/driver-esp32` checkout by
driving its `scripts/flash.sh` (which stamps the version from `git describe`
and merges the variant's manifest). The script is deliberately **not** copied
here: it depends on the checkout's `manifests/`, `firmware/`, `packages/` and
git history, and a copy would drift. The skill instead asks for what is
missing: the variant, the board name (`--board <name>`, each board is its own
Driver `esp32-<name>`), USB first flash vs OTA update, the serial port, and the
board's one secrets file, `secrets/<name>.yaml` (WiFi, broker account, OTA
password, BLE wake secret; it never prints or commits it). It checks
`esphome` and the layout, warns about `-dirty` versions and the relay board's
`OE` pull-up, then verifies the board's retained state, info and health topics
on the bus.

See `skills/renewvan-flash-esp32/SKILL.md` for the full process.

### `renewvan-create-driver`

Bootstraps a new `renewvan/driver-<entity>` repo: MQTT publisher skeleton,
layered `config.default.ini`/`config.ini` loader, `manifest.json` + retained
Driver info, systemd unit, Dockerfile, CI (tests, manifest gate, release) — rendered from the `renewvan/driver-template` repo, the reference skeleton for
every `driver-*` repo. Scaffolds only; it deliberately does not implement the
device's sensing/publishing logic, and ends by running a fixed design round
(sensing-vs-remapping, published fields, hub schema, hardware config, hub
integration) so a real device still gets designed, not left half-built.

See `skills/renewvan-create-driver/SKILL.md` for the full process.

### `renewvan-build-basemap`

Builds the dashboard's offline `basemap.pmtiles` for a region, city or country
by name: resolves the area to a bounding box (or outline) via Nominatim, picks
a Protomaps v4 build, dry-runs `pmtiles extract` to size it, extracts,
verifies the file (including that tiles exist under a given point), and
optionally pushes it to the Pi with the hub's script. Follows
`renewvan/dashboard`'s `docs/offline-map.md`; the self-build from OpenStreetMap
route is out of scope.

See `skills/renewvan-build-basemap/SKILL.md` for the full process.

## Development

`scripts/build_claude.py` generates `claude/` from `skills/` (see
"Variants and versions"); commit both.

`skills/renewvan-create-driver/scripts/scaffold.py` is the one piece of real code
here — everything else is markdown/templates. `tests/test_scaffold.py`
exercises it end to end (scaffolds into a temp dir, asserts the layout and
token substitution). Run before opening a PR:

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

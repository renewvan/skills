---
name: scaffold-node
description: Bootstrap a new renewvan/node-<entity> repo (MQTT skeleton, layered config, systemd unit, Dockerfile, CI) from the node-tank reference shape, then run a design round for its topics and hardware interface. Use when the user wants to scaffold a new renewvan node, create node-<entity>, or start integrating a new device into the renewvan hub.
---

# Scaffold a renewvan node

Generates a new `node-<entity>` repo in the shape `renewvan/node-tank`'s
README documents as the reference for every `node-*` repo: a pure-function
core, a layered `config.default.ini`/`config.ini` loader, a persistent MQTT
publisher with LWT, a thin publish loop, a systemd unit, and its own
Dockerfile + CI. This skill bootstraps that skeleton only —
`driver.py`'s read-publish step ships as a deliberate `NotImplementedError`.
Design and implementation are Step 5, not this skill's job to finish.

## Step 1 — Collect scaffold inputs

Ask the user directly (these are mechanical inputs, not open design
decisions):

- **Entity slug**: lowercase, `[a-z][a-z0-9_]*` (e.g. `gps`). Becomes the
  topic segment (`renewvan/gps/...`), the Python package (`node_gps`), and
  the repo name (`node-gps`).
- **One-line description** for `pyproject.toml`/README/GitHub repo
  description.
- **Target directory**. Default: a `node-<entity>` sibling next to whichever
  `renewvan/*` repo the agent is currently in (e.g. `../node-gps` next to
  `hub`) — ask only if that default is ambiguous.
- **Publish to GitHub?** If yes, needs `gh` authenticated against the
  `renewvan` org (`gh auth status`); if no org access, scaffold locally only
  and say so.

## Step 2 — Generate

```
python3 scripts/scaffold.py <entity-slug> "<Entity Title>" "<description>" <target-dir>
```

Resolve `scripts/scaffold.py` against this skill's own directory (see the
`[Skill directory: …]` footer on this message), not the target repo. The
script copies `templates/node-skeleton/`, substitutes
`__ENTITY__`/`__ENTITY_TITLE__`/`__PACKAGE__`/`__REPO__`/`__DESCRIPTION__`/
`__YEAR__` in every path and file, renames the package directory, and strips
`.tmpl` suffixes — it is deterministic; don't hand-copy or retype any
template file yourself. Refuses to run over an existing target directory
and rejects a malformed entity slug.

## Step 3 — Commit and publish

```
cd <target-dir> && git init -b main && git add -A && git commit -m "Scaffold node-<entity> from the node-tank reference shape"
```

If GitHub was requested:

```
gh repo create renewvan/node-<entity> --public --source=. --remote=origin --push
```

## Step 4 — Smoke-verify

```
pip install -r requirements.txt -r requirements-test.txt && pytest tests/ -v
```

Must pass out of the box (defaults only, no hardware/broker needed) — the
scaffolded test only exercises `config.py`'s layered loader. A failure here
means the scaffold itself is broken, not the (intentionally unimplemented)
driver.

## Step 5 — Hand off to design

The repo is a shell, not a node yet: `driver.py`'s `read_and_publish()`
raises `NotImplementedError`, and `config.py`'s `NodeConfig` has no
hardware-specific fields. Tell the user this plainly, then run this fixed
design round (same question-then-wait shape as the `grilling` skill, scoped
to exactly these five questions — don't open-end it into a full grilling
session unless the user asks for one):

```
❓ Q1 - Sensing or remapping?: Does this node own the sensing (reads a
physical sensor/bus directly, like node-tank's ADS1115) or remap an
existing feed (subscribes to a vendor's own MQTT/API and republishes, like
node-battery's Victron remap)? This decides driver.py's shape.

❓ Q2 - Published fields: What properties does renewvan/<entity>/<id>/
<property> publish, and which are identity (published once) vs live
(republished every poll)? See node-tank README's "Topics published"
section for the split.

❓ Q3 - New hub schema entity, or does this extend one of tank/relay/
battery/router? If new, it needs hub/schema/<entity>.schema.json + example
fixtures (hub/schema/validate-examples.sh must pass).

❓ Q4 - Hardware interface: what config keys does NodeConfig need (serial
port, I2C address, remote host, baud rate, polling interval)? These go in
both config.py's NodeConfig dataclass and config.default.ini.

❓ Q5 - Hub integration: once a version is tagged and
ghcr.io/renewvan/node-<entity>:<tag> is published, does
hub/docker-compose.yml need a new service block (pattern: node-tank's
block) and hub/.env.example keys? Not yet — only once a real image exists.
```

Wait for answers before writing any implementation code. Once settled,
update `CONTEXT.md` (the field glossary) and the README's "Topics
published"/"Wiring" sections to match — they currently carry `TODO`
markers, not placeholders to leave in place.

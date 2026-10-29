---
name: port-dbus-driver
description: Port a Venus OS D-Bus driver package (dbus-ads1115, dbus_wattcycle_ble, dbus-autoterm, dbus-giandel-bridge) to a native MQTT renewvan driver, following the hub's porting recipe end to end. Use when the user wants to port, migrate or convert a dbus-* package or Venus OS service to MQTT, or replace Venus OS for non-Victron hardware.
license: MIT
metadata:
  version: "1.0.0"
  domain: renewvan
argument-hint: "[dbus-package]"
---

# Port a D-Bus driver to native MQTT

Orchestrates the recipe in `renewvan/hub` `docs/porting-dbus-to-mqtt-driver.md`
(read it first; if this skill and the recipe disagree, the recipe wins).
There is no single mechanical port: the work is a chain of smaller steps, some
of which other skills already do. This skill sequences them and keeps the
hub's rules in view.

Worked example throughout the recipe: `dbus-ads1115` → `renewvan/tank`.

## Step 0 — Scope check

Ask only for what you cannot infer:

- **Which package** is being ported, and where its source checkout is.
- **The hub checkout** (default `../hub` next to this repo).

Stop and say so if the hardware is **genuine Victron gear** (VE.Direct/VE.Can).
That stays on Venus OS and gets a remap-shaped driver (`driver-venus`), which is
not this recipe. This recipe is for community/non-Victron hardware whose sensing
the project owns.

## Step 1 — Inventory the package

Read the source package and write a short port plan for the user, sorted into
the recipe's three buckets. Show it and get a go-ahead before changing code.

- **Strip**: D-Bus service registration (`vedbus.py`, `VeDbusService`, object
  paths), `settingsdevice.py`, Venus OS packaging (SetupHelper `package.json`,
  `/service` daemontools directory, GUI menu, version/upgrade scripts), and GUI
  calibration screens. v0 calibration is config-file only; a calibration UI is
  a dashboard concern.
- **Keep, near-verbatim**: sensor read/decode, unit conversion, calibration
  math and piecewise curves, alarm-threshold logic, and the layered
  `config.default.ini` / `config.ini` pattern.
- **Add**: an MQTT client (retry/backoff, LWT, persistent connection), a
  publish loop onto `renewvan/<entity>/<id>/<property>`, retained-topic
  conventions, and a systemd unit (`Restart=on-failure`,
  `WantedBy=multi-user.target`, one unit per driver process).

## Step 2 — Settle entity, topics and vocabulary

Decide with the user, one question at a time:

- Does the device publish an **existing** entity (battery, tank, relay, router,
  solar, …) or a **new** one? A driver is named for its **source**, not the
  entity it publishes (hub ADR 0008).
- Which properties are **identity** (published once at startup or on config
  reload) and which are **live** (republished on every read)? All are retained;
  the split is only how often they are republished. `id` is the topic segment,
  not a payload field. Publish the retained `driver` property (the Driver key)
  with each instance's identity fields.
- If the source exposes something the entity cannot represent, the path is a
  **hub schema change**, never ad-hoc topics.

If a domain-modeling skill is available, use it for new vocabulary and to
record an ADR; if a grilling skill is available, use it to stress-test the
design. Otherwise ask the questions directly.

## Step 3 — Scaffold the repo

Use the `create-driver` skill with the entity slug from Step 2 (it creates
`driver-<entity>` with the MQTT skeleton, layered config, systemd unit,
Dockerfile, manifest and CI). Its design round overlaps Step 2: carry the
answers over instead of asking again.

## Step 4 — Port the sensing logic, test first

Work test-first (use a TDD skill if available). Port the domain logic from the
source package into pure functions with unit tests against fixture readings,
then wire it into `driver.py`'s `read_and_publish()`. Do the Strip list from
Step 1 as you go: nothing may import `vedbus`, `dbus` or `gi`. Add the
hardware-specific fields to `DeviceConfig` and `config.default.ini`.

Do not change calibration maths while porting; if the original looks wrong,
note it for the user and port it as is.

## Step 5 — Manifest and Driver info

Follow `hub/docs/authoring-a-driver.md`: fill `manifest.json` (`source`,
`publishes`; never `version` or `board_serial`), publish info before `online`,
and let `DRIVER_VERSION` come from the release tag. Validate the manifest
against the hub's `schema/driver-manifest.schema.json`.

## Step 6 — Hub schema, examples and demo (hub repo)

Only when the change needs it:

- **New entity**: add `schema/<entity>.schema.json` and example fixtures
  (`*.valid.json` / `*.invalid.json`), add the entity to the `publishes` enum in
  **both** `driver-manifest.schema.json` and `driver-info.schema.json`, and add
  `schema/demo/<entity>.demo.json` in the same change.
- **New required property** on an existing entity: update its demo scenario.
- **Existing entity, no schema change**: ship no demo and leave `schema/demo/`
  alone; the driver only complies with the schema.

Then run both validators from the hub and report the result of each:

```
./schema/validate-examples.sh
python3 schema/validate-demo.py        # needs: pip install jsonschema
```

## Step 7 — Chase failures

When tests or validators fail, diagnose the cause before patching (use a
diagnosing/debugging skill if available). Fix the root cause, not the test.

## Step 8 — Review

Review the driver repo and any hub changes before merging (use a code-review
skill if available). The hub formats and lints on commit through the pre-commit
hook; do not bypass it.

## Step 9 — Ship

After a release publishes `ghcr.io/renewvan/driver-<entity>:<tag>`:

1. Edit the `image:` tag in the hub's `docker-compose.yml` (the single
   git-tracked source of truth, not `.env`) and add any new `.env.example` keys.
2. Use the `deploy` skill to roll it out to the Pi.

## Do not

- Do not add a Dockerfile or local build to the hub: services ship as pinned
  images.
- Do not publish ad-hoc topics for data the entity schema cannot hold.
- Do not port genuine Victron gear with this recipe.
- Do not port a calibration UI or any Venus OS GUI/QML code.
- `dbus_wattcycle_ble` (battery) and `dbus-autoterm` (heater) are v1 candidates:
  they follow this same recipe against whatever battery/heater schema exists at
  that point.

## Claude Code notes

Invoke as `/port-dbus-driver`. Chain these skills along the steps when
installed: `domain-modeling` and `grilling` (Step 2), `/create-driver`
(Step 3), `tdd` (Step 4), `diagnosing-bugs` (Step 7), `code-review` (Step 8)
and `/deploy` (Step 9). Use the Skill tool to invoke them; do not paraphrase
their procedure from memory.

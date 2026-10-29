---
name: flash-esp32
description: Build and flash a renewvan ESP32 firmware variant (for example esp32-16x-relay) from the driver-esp32 repo over USB or OTA, collecting the WiFi/MQTT secrets and port it needs, then verify the board on the bus. Use when the user wants to flash, reflash, update or OTA an ESP32 board, set up secrets.yaml for it, or check that a flashed relay board works.
license: MIT
metadata:
  version: "1.0.0"
  domain: renewvan
  platforms: esp32
---

# Flash a renewvan ESP32 board

Drives `scripts/flash.sh` in the **`renewvan/driver-esp32` checkout**. Source of
truth: that repo's `README.md` ("Building and flashing", "Version stamp",
"Acceptance"); if this skill and the README disagree, the README wins.

This skill does not contain the build logic and must never replace
`scripts/flash.sh` with a hand-written `esphome run`. The script stamps the
firmware version from the checkout's `git describe` and merges
`manifests/<variant>.json` into the build; a bare `esphome run
firmware/<variant>.yaml` fails on purpose (the Driver identity would be the
literal `${driver}`). It also cannot be copied elsewhere: it needs the
checkout's `manifests/`, `firmware/`, `packages/` and git history.

## Step 0 — Find the checkout and tools

Confirm `scripts/flash.sh` and `manifests/` exist in the working directory or
in `../driver-esp32` (`cd` there if so). If not, stop and tell the user to
clone `renewvan/driver-esp32`.

Check `esphome version` works. If not, tell the user to `pip install esphome`
(ideally in a venv) and stop until it does. Do not install it silently.

## Step 1 — Collect what is missing

Ask only for what you cannot infer. These are mechanical inputs:

- **Variant**: run `scripts/flash.sh --list`. If there is one, use it and say
  so; otherwise ask which (`esp32-16x-relay` is the relay board).
- **First flash or update?** First flash is **USB** (board connected to this
  machine). An update can go **OTA** over WiFi once the board has joined the
  network, using the OTA password in `secrets.yaml`.
- **Serial port** (USB only): list candidates (`ls /dev/cu.usb* /dev/ttyUSB*
  /dev/ttyACM*`) and ask which when there is more than one. If the board is not
  listed, suggest a data (not charge-only) cable and that ESP32 dev boards may
  need the BOOT button held while flashing.
- **Release or working tree?** Prefer flashing from a release tag (`git
  describe` exactly `vX.Y.Z`). Show `scripts/flash.sh --print-version` and
  explain what it will stamp: a `-dirty` or `-N-g<hash>` version means
  uncommitted or untagged code goes on the board. Never refuse; let the user
  decide.

## Step 2 — `secrets.yaml`

ESPHome reads `secrets.yaml` at the repo root (gitignored; `firmware/secrets.yaml`
is a symlink to it). **Never print, log or commit its contents**; when checking
it, only report which keys are present or still equal to the example
placeholders.

If it does not exist, copy `secrets.yaml.example` and ask the user for each
value (they may prefer to type the secret ones into the file themselves; offer
that and wait):

| Key | Ask / default |
| --- | ------------- |
| `wifi_ssid`, `wifi_password` | the van WiFi |
| `wifi_ap_fallback_password` | fallback access point password; must not stay `changeme12345` |
| `ota_password` | their own; must not stay `changeme12345` |
| `api_encryption_key` | generate with `esphome secrets api_encryption_key` or `openssl rand -base64 32`; do not keep the example value |
| `mqtt_broker`, `mqtt_port` | the van's Mosquitto broker (the hub's host) |
| `mqtt_username`, `mqtt_password` | the broker's credentials (may be empty) |

If it exists, ask whether it is current only when a value still looks like an
example placeholder. These values are compiled into the firmware, so a wrong
broker or WiFi means the board will not come up on the van.

## Step 3 — Pre-flight

```bash
python3 scripts/variants.py check     # layout invariants; must pass
git status --short                    # warn about tracked changes: they ship as -dirty
scripts/flash.sh --print-version
```

**Hardware safety, relay board only.** Before connecting any load, confirm the
**external pull-up on `OE` (GPIO5)** is fitted, and that the board's relay
polarity matches it (README "Required: the output-enable pull-up"). Without it
the relays can click on during boot. If the user has not fitted it, flash on the
bench with nothing connected to the relay outputs.

**One board per van.** The Driver key is repo-wide (`esp32`) and relay ids are
fixed (`relay_01`..`relay_16`). A second board, or a second kind of variant,
would overwrite the first board's retained topics and health. If the user says
there is already a board on this bus, stop and point at the README section
"What a variant is, and the Driver key".

## Step 4 — Flash

```bash
scripts/flash.sh <variant>                          # esphome picks the port / OTA
scripts/flash.sh <variant> --device /dev/ttyUSB0    # a specific serial port
scripts/flash.sh <variant> --device <board-ip>      # OTA to a known address
```

Extra arguments pass straight to `esphome run`. The build can take minutes the
first time. Do not interrupt a flash; if it fails, report the error and the
step that failed instead of retrying blindly. If the script says
`unknown variant` or `produced no substitutions; refusing to flash`, fix the
manifest or variant name, never bypass the script.

## Step 5 — Verify on the bus

CI cannot exercise the board, so verify by hand with the broker's address from
Step 2 (`mosquitto_sub` / `mosquitto_pub` from the `mosquitto-clients` package):

```bash
mosquitto_sub -h <broker> -v 'renewvan/#'
```

Reset the board and expect, in order: the sixteen `renewvan/relay/<id>/state`
topics (each with `driver` = `"esp32"`), then `renewvan/esp32/info` (version
equals what Step 1 showed; `ip` equals the address on the router), then
`renewvan/esp32/health` = `online`.

Then, with **no load connected unless the user confirms it is safe**:

```bash
mosquitto_pub -h <broker> -t renewvan/relay/relay_01/set -m true    # state becomes true
mosquitto_pub -h <broker> -t renewvan/relay/relay_01/set -m false
```

Report each check as passed, failed or not run. The full acceptance list
(20+ reset bench test with the pull-up, no 15-minute reboot, rename persists
after 60 s, unplugging the network sets `health` to `offline` while `info`
stays) is in the README; offer to walk through it before the board goes in the
van.

## Do not

- Do not run `esphome run firmware/<variant>.yaml` directly.
- Do not download or flash a CI-built binary: it holds placeholder secrets and a
  known OTA password. Always build from the user's checkout and `secrets.yaml`.
- Do not commit, echo or paste `secrets.yaml`.
- Do not add `api:` or `web_server:` to a firmware to make flashing easier; the
  relay contract forbids both.
- Do not drop the `dev` default of `substitutions.version` in
  `packages/base.yaml`.

---
name: renewvan-flash-esp32
description: Build and flash a renewvan ESP32 firmware variant (for example esp32-16x-relay) from the driver-esp32 repo over USB or OTA, collecting the WiFi/MQTT secrets and port it needs, then verify the board on the bus. Use when the user wants to flash, reflash, update or OTA an ESP32 board, set up secrets.yaml for it, or check that a flashed relay board works.
license: MIT
metadata:
  version: "3.0.0"
  domain: renewvan
  platforms: esp32
argument-hint: "[variant]"
allowed-tools: Bash, Read
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
literal `${driver}`). Every board is flashed with `--board <name>`, which makes it
its own Driver `esp32-<name>`. It also cannot be copied elsewhere: it needs the
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
- **Board name**: the name this physical board keeps for good (`--board <name>`):
  a slug (lowercase letters and digits, hyphens between words), at most 16
  characters, not ending in `-<digits>`. Ask for it; for a second board of a
  variant that is already on the van, ask for a *different* name. Check it with
  `python3 scripts/variants.py board <name>`. Reflashing with the same name keeps
  the same Driver; a new name is a new Driver (old retained topics are cleared
  by hand, see README).
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

## Step 2 — Secrets (shared file plus one per board)

Secrets are per board. `secrets.yaml` at the repo root (gitignored) holds what
every board of the van shares; `secrets/<board>.yaml` (gitignored) holds the
board's own, and its keys win. `scripts/flash.sh` merges them and refuses a
board that has no `secrets/<board>.yaml`. **Never print, log or commit either
file**; when checking them, only report which keys are present or still equal to
the example placeholders.

If a file does not exist, copy `secrets.yaml.example` (`mkdir -p secrets` for the
board file) and ask the user for each value (they may prefer to type the secret
ones into the file themselves; offer that and wait):

| File | Key | Ask / default |
| ---- | --- | ------------- |
| `secrets.yaml` | `wifi_ssid`, `wifi_password` | the van WiFi |
| `secrets.yaml` | `wifi_ap_fallback_password` | fallback access point password; must not stay `changeme12345` |
| `secrets.yaml` | `mqtt_broker`, `mqtt_port` | the van's Mosquitto broker (the hub's host) |
| `secrets/<board>.yaml` | `mqtt_username`, `mqtt_password` | the board's broker account: username `esp32-<board>`, password the hub's `MQTT_ESP32_<BOARD>_PASSWORD` (the board must be listed in the hub's `BROKER_ESP32_BOARDS`) |
| `secrets/<board>.yaml` | `ota_password` | its own; must not stay `changeme12345` |
| `secrets/<board>.yaml` | `api_encryption_key` | generate with `esphome secrets api_encryption_key` or `openssl rand -base64 32`; do not keep the example value |
| `secrets/<board>.yaml` | `ota_address` | optional: the board's IP, used as the OTA target when `--device` is not given |

If the files exist, ask whether they are current only when a value still looks
like an example placeholder. These values are compiled into the firmware, so a
wrong broker, account or WiFi means the board will not come up on the van.

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

**A second board.** Any number of boards can share a van, each its own Driver,
as long as each has a different `--board` name and its own
`secrets/<board>.yaml`. Nothing checks that a name is unused: reusing a name that
another board already holds overwrites that board's retained topics. If unsure,
offer the best-effort check from the README (`mosquitto_sub -C 1 -W 3 -t
'renewvan/esp32-<board>/info'`) before the first flash.

## Step 4 — Flash

```bash
scripts/flash.sh <variant> --board <name>                        # OTA to its ota_address, else esphome picks the port / OTA
scripts/flash.sh <variant> --board <name> --device /dev/ttyUSB0  # a specific serial port
scripts/flash.sh <variant> --board <name> --device <board-ip>    # OTA to a known address
```

Extra arguments pass straight to `esphome run`. An OTA update only reaches the named board, with that board's `ota_password`. The build can take minutes the
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

Reset the board and expect, in order: its relay states
`renewvan/relay/<board>-<nn>/state` (each with `driver` = `"esp32-<board>"`; `<nn>`
is `01`..`16`, or `01`..`08` on the 8x variant), then `renewvan/esp32-<board>/info`
(version equals what Step 1 showed; `variant` is the firmware kind; `ip` equals the
address on the router), then `renewvan/esp32-<board>/health` = `online`. With two
boards, confirm the other board's topics are unchanged.

Then, with **no load connected unless the user confirms it is safe**:

```bash
mosquitto_pub -h <broker> -t renewvan/relay/<board>-01/set -m true    # state becomes true
mosquitto_pub -h <broker> -t renewvan/relay/<board>-01/set -m false
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
- Do not commit, echo or paste `secrets.yaml` or any `secrets/<board>.yaml`.
- Do not reuse one board's `secrets/<board>.yaml` for another board.
- Do not add `api:` or `web_server:` to a firmware to make flashing easier; the
  relay contract forbids both.
- Do not drop the `dev` default of `substitutions.version` in
  `packages/base.yaml`.

## Claude Code notes

Invoke as `/flash-esp32`. Flashing runs for minutes and writes to hardware: run
`scripts/flash.sh` in the foreground so the output is visible, and use
AskUserQuestion for the Step 1 choices (variant, USB vs OTA, serial port). Never
Read or Edit `secrets.yaml` to display it; check keys with a pattern that
prints only key names.

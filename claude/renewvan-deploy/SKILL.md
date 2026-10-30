---
name: renewvan-deploy
description: Use when deploying the renewvan hub to the Raspberry Pi — running bin/deploy.sh, checking whether a deploy is needed, or verifying a deploy succeeded.
license: MIT
metadata:
  version: "2.0.0"
  domain: renewvan
  platforms: raspberry-pi
allowed-tools: Bash
argument-hint: "[--host <ssh-alias>]"
---

# renewvan hub deploy

Deploy the hub (`bin/deploy.sh`) to the Pi over SSH. The script is idempotent — safe to re-run.

Run everything from the **`renewvan/hub` checkout** (the script and `docker-compose.yml` live there). The hub also ships its own copy of this skill under `.agents/skills/deploy`; this one is the same procedure packaged for installing elsewhere.

## Step 0 — Find the hub checkout

This skill only drives `bin/deploy.sh`; it does not contain the deploy logic
and must never reimplement it by hand. Confirm the working directory, or
`../hub` (`cd` there if so), is the hub checkout:

```bash
test -f bin/deploy.sh && test -f docker-compose.yml && test -f bin/bootstrap-pi.sh \
  && head -1 CONTEXT.md | grep -qx '# renewvan Hub' && echo "hub checkout"
```

All four must hold: other repos can also have a `bin/deploy.sh` and
`docker-compose.yml`, and running one of those against the Pi is the failure
this check prevents. If neither location passes, stop and tell the user to
clone `renewvan/hub` first (`git clone git@github.com:renewvan/hub.git`) or
`cd` into their checkout. Never run `bin/deploy.sh` from a directory that
failed the check.

Prerequisites: `ssh` and `rsync` locally, an `renewvan` SSH alias (or pass
`--host`), and a Pi already prepared with the hub's `bin/bootstrap-pi.sh`
(kiosk display: `bin/bootstrap-kiosk-pi.sh`). A brand-new Pi must be
bootstrapped before its first deploy.

## SSH target

Default host alias: `renewvan`. Override with `--host <alias-or-user@host>`.

## Pre-flight

Run these before `bin/deploy.sh`:

**1. Pi reachable?**
```bash
ssh renewvan exit
```
If this fails, stop and surface the SSH error. Do not proceed.

**2. Uncommitted local changes?**
```bash
git status --short
```
If dirty, warn the user — list the changed files — and ask whether to continue. The script rsyncs the working tree, so uncommitted changes go to the Pi.

## Run the deploy

```bash
bin/deploy.sh
# or with a non-default host:
bin/deploy.sh --host <alias>
```

The script: rsyncs compose artifacts and plugins → creates/updates venvs in `/opt/renewvan/venvs/` → enables systemd services → runs `docker compose pull && up -d`. Flags and full flow: read `bin/deploy.sh`.

## Post-deploy verification

```bash
ssh renewvan docker compose -f /opt/renewvan/hub/docker-compose.yml ps
```

All services should show `running`. Any service in `exited` or `restarting` → pull its logs:

```bash
ssh renewvan docker compose -f /opt/renewvan/hub/docker-compose.yml logs --tail=50 <service>
```

## Service restarts after deploy

`docker compose up -d` restarts any container whose image or config changed — no manual step needed.

Systemd plugin services (`renewvan-kiosk`, `renewvan-tailscale`) are handled differently. The deploy script runs `systemctl daemon-reload` and `enable --now`, which starts them if stopped but **does not restart a running service**. If you changed a `.service` file or its `ExecStart` target, restart manually:

```bash
ssh renewvan sudo systemctl restart renewvan-kiosk
ssh renewvan sudo systemctl restart renewvan-tailscale
```

Verify the new config is live:
```bash
ssh renewvan systemctl show renewvan-kiosk --property=ExecStart
```

A full Pi reboot is never required for hub deploys.

## Kiosk display refresh

`bin/deploy.sh` automatically reloads Chromium on the Pi display after every deploy — kills the running instance and relaunches it in kiosk mode pointing at `http://localhost`. No manual step needed; the new dashboard version appears on the screen within ~5 seconds of deploy completing.

If the display doesn't update after a deploy, reload manually:
```bash
ssh renewvan "pkill chromium || true; sleep 2; WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 nohup chromium --kiosk --ozone-platform=wayland --password-store=basic --noerrdialogs --disable-infobars --disable-session-crashed-bubble --disable-translate --disable-pinch --overscroll-history-navigation=0 --check-for-update-interval=31536000 --no-first-run http://localhost >/dev/null 2>&1 &"
```

## Failure handling

| Symptom | Cause | Fix |
|---|---|---|
| rsync `Permission denied` on remote files | File owned by root in synced dir | The deploy script excludes `.venv` dirs from rsync; if other root-owned files appear, `ssh renewvan sudo chown -R $USER <path>` then re-run |
| `docker compose pull` fails | Registry auth or image tag missing | Check `.env` on the Pi for correct `*_IMAGE_TAG` values; verify the image exists on ghcr.io |
| `docker compose up -d` fails | Port conflict, OOM, bad env | `ssh renewvan docker compose logs <service>` for the root cause |
| `driver-gps` not running after deploy | No `/dev/ttyACM0` on the Pi, so deploy skips the `gps` profile (a missing `devices:` path would otherwise abort the whole `up -d`) | Plug in the GPS module and re-run `bin/deploy.sh`; it enables the profile when the device exists. Manual start: `docker compose --profile gps up -d` |
| SSH times out mid-deploy | Network drop | Re-run `bin/deploy.sh` — it is idempotent |
| `.env` missing on Pi | First deploy | Script seeds from `.env.example` and exits; fill in secrets on the Pi and re-run |
| `tank/config.ini` missing | First deploy | Place calibration file at `/etc/renewvan/tank/config.ini` on the Pi and re-run |

## Claude Code notes

Invoke as `/renewvan-deploy`. Run it with the hub checkout as the working directory.
Treat a failed pre-flight (`ssh renewvan exit`) as a hard stop, and ask before
continuing with uncommitted changes.

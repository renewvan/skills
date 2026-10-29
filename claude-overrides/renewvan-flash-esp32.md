---
argument-hint: "[variant]"
allowed-tools: Bash, Read
---
Invoke as `/flash-esp32`. Flashing runs for minutes and writes to hardware: run
`scripts/flash.sh` in the foreground so the output is visible, and use
AskUserQuestion for the Step 1 choices (variant, USB vs OTA, serial port). Never
Read or Edit `secrets.yaml` to display it; check keys with a pattern that
prints only key names.

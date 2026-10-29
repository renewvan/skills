---
allowed-tools: Bash
argument-hint: "[--host <ssh-alias>]"
---
Invoke as `/deploy`. Run it with the hub checkout as the working directory.
Treat a failed pre-flight (`ssh renewvan exit`) as a hard stop, and ask before
continuing with uncommitted changes.

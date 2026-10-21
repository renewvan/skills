# renewvan/skills

Installable agent skills for the **renewvan** ecosystem (see `renewvan/hub`'s
`CONTEXT.md` for domain vocabulary). One skill today: `scaffold-driver`,
which bootstraps a new `driver-<entity>` repo from `renewvan/driver-tank`'s
reference shape.

## Install

**Manual (works with any harness that reads `.agents/skills/` or
`.claude/skills/` — one level under `skills/`, non-recursive):**

```bash
git clone git@github.com:renewvan/skills.git /tmp/renewvan-skills
mkdir -p ~/.agents/skills
cp -R /tmp/renewvan-skills/skills/scaffold-driver ~/.agents/skills/scaffold-driver
```

Use a project-local `.agents/skills/` instead of `~/.agents/skills/` to scope
the skill to one checkout rather than installing it user-wide.

**Via a GitHub-source skill installer** (if your harness has one — same
shape as installing `mattpocock/skills` or `vercel-labs/skills`): point it
at `renewvan/skills`, skill path `skills/scaffold-driver/SKILL.md`.

## Skills

### `scaffold-driver`

Bootstraps a new `renewvan/driver-<entity>` repo: MQTT publisher skeleton,
layered `config.default.ini`/`config.ini` loader, systemd unit, Dockerfile,
CI — the same shape `driver-tank`'s README documents as the reference for
every `driver-*` repo. Scaffolds only; it deliberately does not implement the
device's sensing/publishing logic, and ends by running a fixed design round
(sensing-vs-remapping, published fields, hub schema, hardware config, hub
integration) so a real device still gets designed, not left half-built.

See `skills/scaffold-driver/SKILL.md` for the full process.

## Development

`skills/scaffold-driver/scripts/scaffold.py` is the one piece of real code
here — everything else is markdown/templates. `tests/test_scaffold.py`
exercises it end to end (scaffolds into a temp dir, asserts the layout and
token substitution). Run before opening a PR:

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

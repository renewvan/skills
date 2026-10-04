# renewvan/skills

Installable agent skills for the **renewvan** ecosystem (see `renewvan/hub`'s
`CONTEXT.md` for domain vocabulary). One skill today: `scaffold-node`,
which bootstraps a new `node-<entity>` repo from `renewvan/node-tank`'s
reference shape.

## Install

**Manual (works with any harness that reads `.agents/skills/` or
`.claude/skills/` — one level under `skills/`, non-recursive):**

```bash
git clone git@github.com:renewvan/skills.git /tmp/renewvan-skills
mkdir -p ~/.agents/skills
cp -R /tmp/renewvan-skills/skills/scaffold-node ~/.agents/skills/scaffold-node
```

Use a project-local `.agents/skills/` instead of `~/.agents/skills/` to scope
the skill to one checkout rather than installing it user-wide.

**Via a GitHub-source skill installer** (if your harness has one — same
shape as installing `mattpocock/skills` or `vercel-labs/skills`): point it
at `renewvan/skills`, skill path `skills/scaffold-node/SKILL.md`.

## Skills

### `scaffold-node`

Bootstraps a new `renewvan/node-<entity>` repo: MQTT publisher skeleton,
layered `config.default.ini`/`config.ini` loader, systemd unit, Dockerfile,
CI — the same shape `node-tank`'s README documents as the reference for
every `node-*` repo. Scaffolds only; it deliberately does not implement the
node's sensing/publishing logic, and ends by running a fixed design round
(sensing-vs-remapping, published fields, hub schema, hardware config, hub
integration) so a real node still gets designed, not left half-built.

See `skills/scaffold-node/SKILL.md` for the full process.

## Development

`skills/scaffold-node/scripts/scaffold.py` is the one piece of real code
here — everything else is markdown/templates. `tests/test_scaffold.py`
exercises it end to end (scaffolds into a temp dir, asserts the layout and
token substitution). Run before opening a PR:

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

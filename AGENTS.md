# hier-config-sde-workflow — Agent and Contributor Guide

This repository holds skills, persona agents, and rules for AI coding tools. It has
no application code. Read `README.md` for the workflow.

## Canonical files

| Content | Canonical location | Rendered by |
|---|---|---|
| Skills | `skills/<name>/SKILL.md` and `skills/<name>/references/` | not rendered; linked as is |
| Personas | `skills/hc-sde-issue/personas/<name>.md` | `scripts/render.py` |
| Language rules | `rules/<lang>.md` | `scripts/render.py` |

Edit only the canonical files. `build/` holds rendered files. Do not commit it.

## Rules

1. **Agent Skills format.** A `SKILL.md` frontmatter has only the keys of the
   specification: `name`, `description`, `license`, `compatibility`, `metadata`
   (string values), `allowed-tools`. `name` matches the folder name. Put a
   tool-specific value under `metadata`.
2. **Persona frontmatter.** `name` (matches the file name), `description`, `tier`
   (`reasoning` or `fast`), `role`, and one optional block for each tool
   (`claude:`). `render.py` copies only the keys that each tool accepts.
3. **Tool-neutral text.** The body of a skill or a persona uses capability terms
   ("start a persona", "ask a choice question", "invoke a skill", "session temporary
   directory"). Tool names of one platform go only in
   `skills/hc-sde-issue/references/platforms.md` and in a frontmatter tool block.
4. **Optional skills.** A call to a skill that not every platform has starts with "If
   the `<name>` skill is available" and gives a fallback.
5. **Prose.** Write all prose in ASD-STE100 Simplified Technical English.
6. **Scope.** The content is for the netdevops repositories. Do not add content that
   is specific to another organization, its repositories, or its issue tracker.
7. **Handoff format.** The headings of the handoff report in
   `skills/hier-config-reviewer/SKILL.md` are a contract with `hc-sde-qa`. Change both
   together.

## Checks before a commit

```bash
bash -n install.sh
python3 scripts/render.py --out "$(mktemp -d)"
HOME="$(mktemp -d)" ./install.sh --tool all
```

Validate each skill with the Agent Skills reference validator
(https://github.com/agentskills/agentskills/tree/main/skills-ref):

```bash
skills-ref validate skills/hc-sde-issue
skills-ref validate skills/hier-config-reviewer
```

Commit messages use the imperative mood and a subject of 72 characters or less.

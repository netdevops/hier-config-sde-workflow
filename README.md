# hier-config-sde-workflow

Skills and persona agents for the software development life cycle of the
[netdevops](https://github.com/netdevops) hier-config repositories. One command takes
a GitHub issue from requirements to a pull request (PR) that is ready for human
review.

```text
/hc-sde-issue #123
```

The skills follow the open [Agent Skills](https://agentskills.io) format. They run in
Claude Code, OpenAI Codex CLI, Gemini CLI, and GitHub Copilot.

## Workflow

```text
GitHub issue ──► assigned, label "in progress"
   │
   ▼
Architect (reasoning) ◄──► User     questions until no gap is open, then plan approval
   │  plan posted as an issue comment
   ▼
Engineer (fast)                     branch u/<github-account>/<issue>-<slug>, TDD,
   │                                simplify, draft PR from the repo PR template,
   │                                "Closes #<issue>", assigned to <github-account>
   ▼
QA (reasoning) ◄──► Engineer        hier-config-reviewer --handoff, fix all in-scope
   │                                findings, 3 rounds maximum
   ▼
UX (reasoning)                      library examples, CLI transcripts, API calls,
   │                                docs screenshots, evidence in the PR
   ▼
PR ready for review ──► label "in review" ──► retrospective posted to the issue
```

| Persona | Agent | Model tier (Claude Code) | Job |
|---|---|---|---|
| Software architect | `hc-sde-architect` | reasoning (`fable`, fallback `opus`) | Read the issue with `gh`. Ask questions. Write the plan. |
| Software engineer | `hc-sde-engineer` | fast (`sonnet`) | Build the plan with TDD and the smallest change. Simplify. Open a draft PR, assigned to your GitHub account. Fix findings. |
| Quality assurance | `hc-sde-qa` | reasoning (`opus`) | Run `hier-config-reviewer --handoff`. Send the in-scope findings to the engineer. |
| UX designer | `hc-sde-ux` | reasoning (`opus`) | Test the user journeys. Record the evidence. Finish the PR description. |

The `hc-sde-issue` skill runs in your session and orchestrates the personas. A
persona cannot talk to you, so the orchestrator asks you each question and sends
your answer back to the persona.

### Product-minded practices

The personas use practices from "The Product-Minded Software Engineer" by Gergely
Orosz:

- The architect asks why the change is necessary before it decides how to make it.
- The architect gives options with their cost and value, and you choose one.
- The architect lists the edge cases, and you decide for each one: now, later, or out
  of scope.
- The plan states a success measure, including how you know that it works after the
  release.
- The engineer writes the first test from an acceptance criterion.
- The UX persona tests the full user journey, from how a user finds the feature.
- The plan comment on the issue starts with the problem, the decision, and the scope,
  for a product manager.
- A retrospective goes to the issue at the end: what the plan got wrong, and one
  lesson.

### Outputs

| Output | Location |
|---|---|
| Plan, QA reports, UX report | `<session temporary directory>/hc-sde-<repo>-<issue>/` |
| Plan and retrospective | Comments on the GitHub issue |
| Issue status | Assignee, and the label `in progress` at the start, `in review` when the PR is ready |
| Code | Branch `u/<github-account>/<issue>-<slug>` |
| Screenshots | Orphan branch `sde-assets` of the repository, folder `<issue>/` |
| CLI transcripts | `## UX evidence` section of the PR description |
| Out-of-scope QA findings | `## Workflow notes` section of the PR description |

The workflow does not close the issue. The `Closes #<issue>` line of the PR closes it
when a human merges the PR.

## Skills

- `hc-sde-issue` — the workflow. Start it with `/hc-sde-issue <issue>`. The issue can
  be `#123`, `123`, `<owner>/<repo>#123`, or an issue URL.
- `hier-config-reviewer` — one consolidated review before a PR. Start it with
  `/hier-config-reviewer [PR | branch | path]`. It runs the language gates, one
  standards review for each language (Python, Rust, Go), the in-repo review skill (for
  example `hier-config-review` in `hier_config`), a security review, and a code review.
  It judges the existing PR comments and checks the changelog entry. The `--handoff`
  argument returns the findings as a report, and it posts no comments. The QA persona
  uses this mode.

## Language standards

| Language | Review reference | Rule file |
|---|---|---|
| Python | `skills/hier-config-reviewer/references/python.md` | `rules/python.md` |
| Rust | `skills/hier-config-reviewer/references/rust.md` | `rules/rust.md` |
| Go | `skills/hier-config-reviewer/references/go.md` | `rules/go.md` |

The review reference is the full checklist that the reviewer uses. The rule file is a
short list of "always" and "never" items that the AI tool loads while it writes code
in a matching file. The `AGENTS.md` and `docs/dev/` of a repository override both.

## Changelog

The reviewer and the engineer support two methods. They detect the method from the
repository:

- towncrier: a `[tool.towncrier]` table in `pyproject.toml`, or `towncrier.toml`. The
  fragment name is `<issue>.<type>`, for example `changes/123.fixed`.
- Keep a Changelog: `CHANGELOG.md` with a `## [Unreleased]` section. The entry ends
  with `(#<issue>)`.

## Requirements

- An AI coding tool: Claude Code, Codex CLI, Gemini CLI, or GitHub Copilot.
- `git`, and `gh` authenticated with the `repo` scope (`gh auth status`). The account
  needs write access to the repository to assign issues and add labels.
- Python 3.10 or later, for `install.sh`.
- Docker, for the Playwright screenshots of the UX persona. Optional.
- The toolchain of the target repository: Poetry or uv, `cargo`, or `go`.
- Optional skills. The workflow uses them when they are available, and it has a
  fallback when they are not: `simplify`, `code-review`, `security-review`,
  `superpowers:test-driven-development`, and `superpowers:receiving-code-review`.

## Install

Clone the repository. Then run the install script for your AI tools.

```bash
git clone git@github.com:netdevops/hier-config-sde-workflow.git
cd hier-config-sde-workflow
./install.sh --tool claude              # default
./install.sh --tool codex --tool gemini
./install.sh --tool all
```

The script renders the tool-specific persona files into `build/`, then links the
files into these directories:

| Tool | Skills | Personas |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `~/.claude/agents/*.md` |
| Codex CLI | `~/.agents/skills/` | `~/.codex/agents/*.toml` |
| Gemini CLI | `~/.agents/skills/` | `~/.gemini/agents/*.md` |
| GitHub Copilot | `~/.agents/skills/` | `~/.copilot/agents/*.agent.md` |

If a skill or an agent with the same name already exists and it is not a link to this
repository, the script does not change it. Remove the old copy, then run the script
again.

After you change a persona file or a rule file, run the script again. It renders the
files again. Start a new session of your AI tool after the install.

### Language rules for one repository

The rule files are for one repository at a time, so that they do not load in other
projects:

```bash
./install.sh --tool claude --tool copilot --project ~/code/hier_config
```

| Tool | Rule location in the repository |
|---|---|
| Claude Code | `.claude/rules/hc-<lang>.md` |
| GitHub Copilot | `.github/instructions/hc-<lang>.instructions.md` |
| Codex CLI, Gemini CLI | No path-scoped rules. The skills read the review references. |

The script adds each rule path to `.git/info/exclude` of that repository, so that git
does not show the files as changes.

## Other AI tools

The skills use capability terms, for example "start a persona" and "ask a choice
question". `skills/hc-sde-issue/references/platforms.md` maps each term to the tools
of each platform.

If a tool cannot start subagents, the orchestrator uses single-session mode: it takes
the role of each persona in order, from the persona files in
`skills/hc-sde-issue/personas/`. The files in the run directory hold the state
between the personas, so the result is the same.

## Layout

```text
skills/
  hc-sde-issue/
    SKILL.md
    personas/            canonical persona definitions
    references/
      platforms.md       capability terms for each AI tool
  hier-config-reviewer/
    SKILL.md
    references/          python.md, rust.md, go.md
rules/                   python.md, rust.md, go.md (path-scoped rules)
scripts/render.py        renders the persona and rule files for each tool
install.sh
build/                   rendered files (not committed)
```

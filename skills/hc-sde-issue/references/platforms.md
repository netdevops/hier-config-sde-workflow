# Platform terms

The skills of this workflow use capability terms. This file maps each term to the
tools of each supported platform. If your platform is not in a table, use the
closest tool. If no tool gives the capability, use the fallback.

## Capabilities

| Term | Claude Code | Codex CLI | Gemini CLI | GitHub Copilot |
|---|---|---|---|---|
| Start a persona | `Agent` tool with `subagent_type: "<persona>"` | Start the custom agent `<persona>` | Delegate to the subagent `<persona>` | Delegate to the custom agent `<persona>` |
| Resume a persona | `SendMessage` to the agent id | Fallback below | Fallback below | Fallback below |
| Ask a choice question | `AskUserQuestion` (up to 4 questions, option `preview`) | Numbered options as text; wait for the reply | Numbered options as text; wait for the reply | Numbered options as text; wait for the reply |
| Invoke a skill | `Skill` tool with the skill name | Load the skill by name | `activate_skill` with the skill name | Load the skill by name |
| Session temporary directory | The scratchpad directory of the session | A new directory from `mktemp -d` | A new directory from `mktemp -d` | A new directory from `mktemp -d` |

Fallback for "resume a persona": if the platform cannot send a message to a running
subagent, start the persona again. Give it the original prompt, the new message,
and the list of files that it wrote in `RUN_DIR`. If the platform cannot start a
subagent at all, use single-session mode (see `SKILL.md`).

Fallback for "ask a choice question": write each question with its options as a
numbered list. Mark the recommended option. Stop your turn, and wait for the reply.

## Model tiers

| Tier | Claude Code | Other platforms |
|---|---|---|
| reasoning | `fable`. If the `fable` usage limit is reached, or the model is not available, use `opus`. | The strongest model that the user has configured |
| fast | `sonnet` | The default model |

Model fallback rule for Claude Code: if the architect cannot start on `fable`,
start a new `hc-sde-architect` agent with `model: "opus"`. Give it the same prompt.
If the old agent was in progress, add each question and each answer of the user so
far, quoted, and the paths of the files that the old agent wrote in `RUN_DIR`.
Tell the user that the architect now uses `opus`, and why. Use the new agent id for
all later messages, and use `opus` for each later start of the architect in the run.

## Installed locations

`install.sh` puts the files in these directories. See the README for the install
command.

| Item | Claude Code | Codex CLI | Gemini CLI | GitHub Copilot |
|---|---|---|---|---|
| Skills | `~/.claude/skills/<name>/` | `~/.agents/skills/<name>/` | `~/.agents/skills/<name>/` | `~/.agents/skills/<name>/` |
| Personas | `~/.claude/agents/<persona>.md` | `~/.codex/agents/<persona>.toml` | `~/.gemini/agents/<persona>.md` | `~/.copilot/agents/<persona>.agent.md` |
| Language rules (per repository) | `.claude/rules/hc-<lang>.md` | none: the skills read `references/<lang>.md` | none: the skills read `references/<lang>.md` | `.github/instructions/hc-<lang>.instructions.md` |

Optional skills: the workflow uses these skills when they are available. If a skill
is not available, the step that calls it gives a fallback.

- `simplify`, `code-review`, `security-review` (Claude Code)
- `superpowers:test-driven-development`, `superpowers:receiving-code-review`
  (the superpowers skill set)

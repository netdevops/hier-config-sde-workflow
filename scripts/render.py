#!/usr/bin/env python3
"""Render the tool-specific persona and rule files from the canonical sources.

The canonical personas are in skills/hc-sde-issue/personas/*.md. The canonical
rules are in rules/*.md. Each AI tool needs a different file form:

| Tool    | Persona file                  | Persona keys                         | Rule file                                    |
|---------|-------------------------------|--------------------------------------|----------------------------------------------|
| claude  | agents/<name>.md              | name, description + the claude block | rules/hc-<lang>.md (paths: list)             |
| codex   | agents/<name>.toml            | name, description, developer_instructions | none                                    |
| gemini  | agents/<name>.md              | name, description                    | none                                         |
| copilot | agents/<name>.agent.md        | name, description                    | instructions/hc-<lang>.instructions.md (applyTo) |

Sources for the forms (checked 2026-09-22):
- Claude Code: https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/memory
- Codex CLI: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Gemini CLI: https://geminicli.com/docs/core/subagents/
- Copilot: https://docs.github.com/en/copilot/reference/custom-agents-configuration,
  https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions

The frontmatter parser reads only the subset that the canonical files use:
"key: value" lines, one level of nested mapping, and lists of "- value" items.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent
PERSONA_DIR = REPO_DIR / "skills" / "hc-sde-issue" / "personas"
RULE_DIR = REPO_DIR / "rules"
TOOLS = ("claude", "codex", "gemini", "copilot")
CLAUDE_AGENT_KEYS = ("model", "tools", "disallowedTools", "color")

Frontmatter = dict[str, "str | list[str] | dict[str, str]"]


def split_frontmatter(text: str, path: pathlib.Path) -> tuple[Frontmatter, str]:
    """Return the parsed frontmatter and the body of a markdown file."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise SystemExit(f"{path}: no frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        raise SystemExit(f"{path}: frontmatter has no end marker") from None
    return parse_frontmatter(lines[1:end], path), "".join(lines[end + 1 :]).lstrip("\n")


def parse_frontmatter(lines: list[str], path: pathlib.Path) -> Frontmatter:
    data: Frontmatter = {}
    key = ""
    for raw in lines:
        line = raw.split(" #", 1)[0].rstrip()
        if not line:
            continue
        if not line.startswith(" "):
            key, _, value = line.partition(":")
            value = value.strip()
            data[key] = unquote(value) if value else {}
            continue
        item = line.strip()
        if item.startswith("- "):
            current = data.get(key)
            data[key] = [
                *(current if isinstance(current, list) else []),
                unquote(item[2:]),
            ]
        elif ":" in item and isinstance(data.get(key), dict):
            sub_key, _, sub_value = item.partition(":")
            nested = data[key]
            assert isinstance(nested, dict)
            nested[sub_key.strip()] = unquote(sub_value.strip())
        else:
            raise SystemExit(f"{path}: cannot parse frontmatter line: {raw.rstrip()}")
    return data


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def yaml_value(value: str) -> str:
    """Quote a scalar only when YAML needs it."""
    if (
        value
        and not any(c in value for c in ":#{}[]&*!|>'\"%@`")
        and value.strip() == value
    ):
        return value
    return json.dumps(value)


def markdown(front: list[tuple[str, str]], body: str) -> str:
    head = "\n".join(f"{key}: {yaml_value(value)}" for key, value in front)
    return f"---\n{head}\n---\n\n{body}"


def render_persona(tool: str, path: pathlib.Path) -> tuple[str, str]:
    """Return the file name and the content of one persona for one tool."""
    data, body = split_frontmatter(path.read_text(), path)
    name, description = str(data["name"]), str(data["description"])
    if name != path.stem:
        raise SystemExit(f"{path}: name {name!r} does not match the file name")
    base = [("name", name), ("description", description)]
    if tool == "claude":
        extra = data.get("claude", {})
        assert isinstance(extra, dict)
        base += [(key, extra[key]) for key in CLAUDE_AGENT_KEYS if key in extra]
        return f"{name}.md", markdown(base, body)
    if tool == "gemini":
        return f"{name}.md", markdown(base, body)
    if tool == "copilot":
        return f"{name}.agent.md", markdown(base, body)
    # codex: TOML. A JSON string is a valid TOML basic string.
    toml = "".join(
        f"{key} = {json.dumps(value)}\n"
        for key, value in (
            ("name", name),
            ("description", description),
            ("developer_instructions", body),
        )
    )
    return f"{name}.toml", toml


def render_rule(tool: str, path: pathlib.Path) -> tuple[str, str] | None:
    """Return the file name and the content of one rule, or None if the tool has no rules."""
    data, body = split_frontmatter(path.read_text(), path)
    globs = data.get("paths")
    if not isinstance(globs, list) or not globs:
        raise SystemExit(f"{path}: 'paths' must be a non-empty list")
    if tool == "claude":
        items = "\n".join(f"  - {json.dumps(glob)}" for glob in globs)
        return f"hc-{path.stem}.md", f"---\npaths:\n{items}\n---\n\n{body}"
    if tool == "copilot":
        return f"hc-{path.stem}.instructions.md", markdown(
            [("applyTo", ",".join(globs))], body
        )
    return None


def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tool", choices=(*TOOLS, "all"), default="all")
    parser.add_argument("--out", type=pathlib.Path, default=REPO_DIR / "build")
    args = parser.parse_args(argv)
    tools = TOOLS if args.tool == "all" else (args.tool,)

    count = 0
    for tool in tools:
        for persona in sorted(PERSONA_DIR.glob("*.md")):
            name, content = render_persona(tool, persona)
            write(args.out / tool / "agents" / name, content)
            count += 1
        for rule in sorted(RULE_DIR.glob("*.md")):
            rendered = render_rule(tool, rule)
            if rendered is not None:
                folder = "instructions" if tool == "copilot" else "rules"
                write(args.out / tool / folder / rendered[0], rendered[1])
                count += 1
    print(f"rendered: {count} files in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

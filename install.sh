#!/usr/bin/env bash
# Install the skills, personas, and rules of this repository for one or more AI tools.
#
#   ./install.sh [--tool claude|codex|gemini|copilot|all]...        user-level skills and personas
#   ./install.sh [--tool ...]... --project <path-to-repository>     per-repository language rules
#
# The default tool is claude. An existing path that is not a link to this repository
# is left in place.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$REPO_DIR/build"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
status=0
tools=()
project=""

usage() {
    sed -n '2,8s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
    exit "${1:-0}"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --tool)
            [ $# -ge 2 ] || usage 2
            case "$2" in
                claude|codex|gemini|copilot) tools+=("$2") ;;
                all) tools+=(claude codex gemini copilot) ;;
                *) echo "unknown tool: $2" >&2; usage 2 ;;
            esac
            shift 2 ;;
        --project)
            [ $# -ge 2 ] || usage 2
            project="$2"
            shift 2 ;;
        -h|--help) usage 0 ;;
        *) echo "unknown argument: $1" >&2; usage 2 ;;
    esac
done
[ ${#tools[@]} -gt 0 ] || tools=(claude)

link() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
        echo "current: $dest"
    elif [ -e "$dest" ] || [ -L "$dest" ]; then
        echo "skipped: $dest exists. Remove it, then run this script again." >&2
        status=1
    else
        ln -s "$src" "$dest"
        echo "linked:  $dest -> $src"
    fi
}

skills_dir() {
    case "$1" in
        claude) echo "$CLAUDE_DIR/skills" ;;
        *) echo "$HOME/.agents/skills" ;;
    esac
}

agents_dir() {
    case "$1" in
        claude) echo "$CLAUDE_DIR/agents" ;;
        codex) echo "$HOME/.codex/agents" ;;
        gemini) echo "$HOME/.gemini/agents" ;;
        copilot) echo "$HOME/.copilot/agents" ;;
    esac
}

# Project rules: tool -> directory in the repository. Tools not listed read the
# language references of the hier-config-reviewer skill.
rules_dir() {
    case "$1" in
        claude) echo ".claude/rules" ;;
        copilot) echo ".github/instructions" ;;
    esac
}

python3 "$REPO_DIR/scripts/render.py" --tool all --out "$BUILD_DIR"

if [ -n "$project" ]; then
    project="$(cd "$project" && pwd)"
    exclude="$(git -C "$project" rev-parse --path-format=absolute --git-path info/exclude)"
    for tool in "${tools[@]}"; do
        rel="$(rules_dir "$tool")"
        if [ -z "$rel" ]; then
            echo "note:    $tool has no path-scoped rules. The skills read the language references."
            continue
        fi
        folder="rules"
        [ "$tool" = copilot ] && folder="instructions"
        for rule in "$BUILD_DIR/$tool/$folder"/*; do
            name="$(basename "$rule")"
            link "$rule" "$project/$rel/$name"
            mkdir -p "$(dirname "$exclude")"
            grep -qxF "/$rel/$name" "$exclude" 2>/dev/null || echo "/$rel/$name" >> "$exclude"
        done
    done
    exit "$status"
fi

for tool in "${tools[@]}"; do
    for skill in "$REPO_DIR"/skills/*/; do
        skill="${skill%/}"
        link "$skill" "$(skills_dir "$tool")/$(basename "$skill")"
    done
    for agent in "$BUILD_DIR/$tool/agents"/*; do
        link "$agent" "$(agents_dir "$tool")/$(basename "$agent")"
    done
done

exit "$status"

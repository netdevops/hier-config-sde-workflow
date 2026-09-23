---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---

# Python rules

These rules apply to the Python code of a hier-config repository. The repository
`AGENTS.md` and `docs/dev/` override a rule when the two disagree. The
`hier-config-reviewer` skill has the full checklist in `references/python.md`.

## Always

- Write the failing test first. Then write the smallest code that makes it pass.
- Annotate every function, method, and test, including the return type.
- Subclass the base model of the project for a Pydantic model. Use `tuple` and
  `frozenset` for model fields.
- Name the code and give the reason in each `# type: ignore[<code>]` and
  `# noqa: <code>`.
- Raise a specific exception. Write an error message that tells the user what to do.
- Use `logging.getLogger(__name__)` in library code.
- Give each new public name a docstring. Update `docs/` when public behavior changes.
- Add a changelog entry that ends with the issue number, for example `(#123)`.
- Run the repository gate before a commit, for example
  `poetry run ./scripts/build.py lint-and-test`.
- Use the tool runner of the repository: `poetry run` or `uv run`.

## Never

- Do not use `Any`, a bare `# type: ignore`, or a bare `# noqa`.
- Do not loosen a lint, type-check, or coverage setting to make a gate pass.
- Do not use `list` or `set` for a field of a frozen model.
- Do not catch `Exception` or use a bare `except:` in library code.
- Do not use `print` in library code.
- Do not add a runtime dependency without an issue that approves it.
- Do not connect to a network device or a network service in a test.
- Do not log a secret or a full device configuration at `INFO` or above.

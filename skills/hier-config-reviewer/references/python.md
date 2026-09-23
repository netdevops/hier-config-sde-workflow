# Python review reference

Use this reference for the Python files of a hier-config repository. The repository
`AGENTS.md`, `CONTRIBUTING.md`, and `docs/dev/` override an item of this file when
the two disagree.

## Gates

Run the repository gate if it exists. Example for `hier_config`:

```bash
poetry run ./scripts/build.py lint-and-test
```

Else run each tool that `pyproject.toml` configures. Use the tool runner of the
repository: `poetry run` if `poetry.lock` exists, `uv run` if `uv.lock` exists.

```bash
<runner> ruff format --check .
<runner> ruff check .
<runner> mypy .
<runner> pyright
<runner> pylint <package> tests
<runner> pytest --cov=<package> --cov-report=term-missing
```

If `docs/` or `mkdocs.yml` changes, also run `<runner> mkdocs build --strict`.

A tool that `pyproject.toml` does not configure is not a gate. Do not add it.

## Typing

- Every function, method, and test has full annotations, including the return type.
- The code does not use `Any`. Use a protocol, a type variable, a union, or
  `object`.
- Each `# type: ignore[<code>]` and `# noqa: <code>` names the code and has a reason
  in the same comment. A bare `# type: ignore` or `# noqa` is a defect.
- Public functions do not return a mutable container that the caller must not change.
  Return a `tuple` or a `frozenset`.
- Use `collections.abc` types for parameters (`Iterable`, `Mapping`, `Sequence`), and
  concrete types for return values.

## Models

- Pydantic models subclass the base model of the project (in `hier_config`:
  `hier_config.models.BaseModel`, which sets `frozen=True` and `extra="forbid"`).
  A model that subclasses `pydantic.BaseModel` directly is a defect if the project
  has its own base model.
- Model fields use immutable collections: `tuple[...]` and `frozenset[...]`, not
  `list` or `set`.
- A default factory is a named module-level function, not a lambda, when the project
  uses that pattern.
- A dataclass that holds state is `frozen=True` unless it must change.

## Configuration

- The diff does not loosen the configuration of ruff, mypy, pyright, pylint, or the
  coverage threshold. It does not add an ignore rule, lower `fail_under`, or add a
  file to an exclude list to make a gate pass.
- A new per-file ignore needs a reason in a comment.

## Tests

- Each change of library behavior has a test. A bug fix has a test that fails before
  the fix.
- Tests are flat functions, not classes, unless the repository uses classes.
- Fixtures live in `tests/conftest.py` and read data from `tests/fixtures/`. A test
  does not read a file with a path relative to the current directory.
- A test asserts one behavior. Its name states the behavior:
  `test_future_removes_negated_line`.
- Parametrize a test with `pytest.mark.parametrize` instead of a loop in the test.
- For remediation logic, the test asserts both directions: the remediation from the
  running to the intended configuration, and the rollback. In `hier_config`, compare
  `dump_simple()` tuples, and assert that `unified_diff` of the rollback is empty.
- The coverage stays at or above the configured threshold (`hier_config`: 95 %).
- A test does not connect to a network device or a network service.

## Errors and logging

- Raise a specific exception class. Do not raise `Exception`.
- Do not catch `Exception` or use a bare `except:`, except at a process boundary
  (a CLI entry point or a request handler), and then log the error.
- The error message tells the user what was wrong and what to do.
- Use `logging.getLogger(__name__)`. Do not use `print` in library code.
- Do not log a secret, a password, or a full device configuration at `INFO` or above.

## Public API and documentation

- A new public function, class, or method has a docstring (PEP 257): one summary
  line, then the arguments, the return value, and the exceptions.
- A change of public behavior updates `docs/` and the README example if one shows it.
- A new page is in the `nav` of `mkdocs.yml`. A moved page has a redirect entry.
- A removed or renamed public name has a deprecation path, or the changelog lists it
  as a breaking change under `Removed` or `Changed`.

## Dependencies

- A new runtime dependency needs an issue that approves it. `hier_config` has one
  runtime dependency (`pydantic`) by design.
- A development dependency goes in the development group, not in the runtime
  dependencies.
- The lock file changes together with `pyproject.toml`.

## Style

- `ruff format` decides the layout. Do not argue with it in a review.
- Use f-strings, not `%` or `str.format`.
- Use `pathlib.Path`, not `os.path`.
- A comment states why, not what.
- Constants are `UPPER_CASE` at module level.

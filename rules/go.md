---
paths:
  - "**/*.go"
  - "**/go.mod"
---

# Go rules

These rules apply to the Go code of a hier-config repository. The repository
`AGENTS.md` and `docs/dev/` override a rule when the two disagree. The
`hier-config-reviewer` skill has the full checklist in `references/go.md`.

## Always

- Write the failing test first. Then write the smallest code that makes it pass.
- Check every returned error. Wrap it with context and `%w`.
- Compare errors with `errors.Is` and `errors.As`.
- Take `ctx context.Context` as the first parameter of a function that does I/O.
- Give each goroutine a clear end.
- Give each exported identifier a doc comment that starts with its name.
- Write table-driven tests with `t.Run`. Put test data in `testdata/`.
- Run `gofmt`, `go vet ./...`, and `go test -race ./...` before a commit.
- Add a changelog entry that ends with the issue number, for example `(#123)`.

## Never

- Do not call `panic`, `log.Fatal`, or `os.Exit` in library code.
- Do not assign an error to `_` without a comment that gives the reason.
- Do not store a `context.Context` in a struct.
- Do not make a network call without a timeout.
- Do not define a large interface in the package that implements it.
- Do not add `//nolint` without the linter name and the reason.
- Do not connect to a network device or a network service in a test.

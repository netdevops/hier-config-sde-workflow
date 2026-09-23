# Go review reference

Use this reference for the Go files of a hier-config repository. The repository
`AGENTS.md`, `CONTRIBUTING.md`, and `docs/dev/` override an item of this file when
the two disagree.

## Gates

```bash
test -z "$(gofmt -l .)"
go vet ./...
go test -race -cover ./...
go mod tidy && git diff --exit-code go.mod go.sum
```

If the repository has `.golangci.yml` or `.golangci.yaml`, also run
`golangci-lint run`. If it has `govulncheck` in CI, also run `govulncheck ./...`.

The gate `go mod tidy` changes files. Run it on a clean tree, and restore the files
with `git checkout -- go.mod go.sum` after the check.

## Errors

- Check every returned error. Do not assign an error to `_` without a comment that
  gives the reason.
- Wrap an error with context: `fmt.Errorf("parse %s: %w", path, err)`. Use `%w`, not
  `%v`, so that the caller can use `errors.Is` and `errors.As`.
- Compare errors with `errors.Is` and `errors.As`, not with `==` or string
  comparison.
- Library code does not call `panic`, `log.Fatal`, or `os.Exit`. Return an error.
- An error string starts with a lowercase letter and has no final period.

## Context and concurrency

- A function that does I/O or can block takes `ctx context.Context` as its first
  parameter. It does not store the context in a struct.
- Each goroutine has a clear end: a closed channel, a cancelled context, or a
  `sync.WaitGroup`. A goroutine that can leak is a defect.
- Shared state is protected by a mutex or owned by one goroutine. The race detector
  must pass.
- A network call has a timeout.

## API design

- Keep interfaces small, and define them in the package that uses them.
- Return concrete types. Accept interfaces.
- A constructor that has many options uses an options struct or functional options.
- The zero value of a type is useful, or the type has a constructor.
- A change of an exported name is a breaking change. A major version change needs a
  new module path (`/v2`).
- The module path is under `github.com/netdevops/`.

## Documentation

- Each exported identifier has a doc comment that starts with its name.
- Each package has a package comment, in `doc.go` if it is long.
- Runnable examples are `Example` functions in `_test.go` files.

## Tests

- Use table-driven tests with `t.Run` for cases of the same behavior.
- Mark helper functions with `t.Helper()`.
- Use `t.TempDir()` for files. Do not write to the source tree.
- Each change of behavior has a test. A bug fix has a test that fails before the fix.
- A test does not connect to a network device or a network service.
- Test data lives in `testdata/`.

## Dependencies

- A new dependency needs a reason in the PR. Prefer the standard library.
- `go.sum` changes together with `go.mod`.
- Do not use a `replace` directive in a released module.

## Style

- `gofmt` decides the layout. Do not argue with it in a review.
- Follow Effective Go and the Go Code Review Comments: short receiver names, no
  `Get` prefix on getters, `MixedCaps` names, initialisms in one case (`URL`, `ID`).
- A `//nolint:<linter>` comment names the linter and gives the reason.
- A comment states why, not what.

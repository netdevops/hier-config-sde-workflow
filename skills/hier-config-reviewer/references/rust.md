# Rust review reference

Use this reference for the Rust files of a hier-config repository. The repository
`AGENTS.md`, `CONTRIBUTING.md`, and `docs/dev/` override an item of this file when
the two disagree.

## Gates

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps --all-features
```

If the repository has `deny.toml`, also run `cargo deny check`. If the crate declares
`rust-version` in `Cargo.toml`, the CI must build with that version. A new API that
needs a newer compiler is a defect.

## Errors

- Library code does not call `unwrap()`, `expect()`, `panic!`, `unreachable!`, or
  `todo!` on a path that user input can reach. Return a `Result`.
  - `expect()` is correct only for an invariant that the code proves. The message
    states the invariant.
  - Tests and examples can use `unwrap()`.
- A library defines its error type with `thiserror`, or with a hand-written `enum`
  that implements `std::error::Error`. A binary can use `anyhow`. A library does not
  expose `anyhow::Error` in its public API.
- Error variants carry the context that the caller needs: the input, the line
  number, or the path.
- Do not convert an error to a `String` if the caller can need to match on it.

## Safety

- Each `unsafe` block has a `// SAFETY:` comment that states why the block is sound.
- A crate with no `unsafe` code has `#![forbid(unsafe_code)]`.
- Do not add `unsafe` to fix a borrow checker error.

## API design

- Follow the Rust API Guidelines (https://rust-lang.github.io/api-guidelines/):
  naming (`as_`, `to_`, `into_`), common traits (`Debug`, `Clone`, `PartialEq`,
  `Default` where they apply), and conversion traits (`From`, `TryFrom`).
- Parameters take a borrowed type where possible: `&str`, not `&String`; `&[T]`, not
  `&Vec<T>`; `impl AsRef<Path>` for paths.
- A public `enum` or `struct` that can grow has `#[non_exhaustive]`.
- A change of a public item is a semver change. Check it with
  `cargo semver-checks` if the repository uses it, and record it in the changelog.

## Documentation

- Each public item has a `///` doc comment. The crate root has a `//!` summary.
- A function that returns `Result` has an `# Errors` section. A function that can
  panic has a `# Panics` section.
- Doc examples compile and run as doc tests.

## Tests

- Unit tests are in a `#[cfg(test)] mod tests` in the same file. Integration tests
  are in `tests/`.
- Each change of behavior has a test. A bug fix has a test that fails before the fix.
- A test does not connect to a network device or a network service.
- Test data lives in `tests/fixtures/`, read with `env!("CARGO_MANIFEST_DIR")`.

## Performance and concurrency

- Do not clone a large value to satisfy the borrow checker when a borrow works.
- Do not hold a lock across an `.await`.
- An async function does not call a blocking function. Use `spawn_blocking`.

## Dependencies

- A new dependency needs a reason in the PR. Prefer the standard library.
- Turn off default features that the crate does not need.
- A binary commits `Cargo.lock`. A library follows the policy of the repository.

## Style

- `rustfmt` decides the layout. Do not argue with it in a review.
- A `#[allow(clippy::...)]` has a comment that gives the reason. Prefer
  `#[expect(...)]` when the MSRV allows it.
- A comment states why, not what.

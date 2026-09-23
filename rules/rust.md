---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust rules

These rules apply to the Rust code of a hier-config repository. The repository
`AGENTS.md` and `docs/dev/` override a rule when the two disagree. The
`hier-config-reviewer` skill has the full checklist in `references/rust.md`.

## Always

- Write the failing test first. Then write the smallest code that makes it pass.
- Return `Result` from a function that can fail on user input.
- Define library errors with `thiserror` or a hand-written error `enum`.
- Write a `// SAFETY:` comment for each `unsafe` block.
- Give each public item a `///` doc comment, with `# Errors` and `# Panics` sections
  where they apply.
- Take borrowed parameters: `&str`, `&[T]`, `impl AsRef<Path>`.
- Add `#[non_exhaustive]` to a public `enum` or `struct` that can grow.
- Run `cargo fmt --all`, `cargo clippy --all-targets --all-features -- -D warnings`,
  and `cargo test --all-features` before a commit.
- Add a changelog entry that ends with the issue number, for example `(#123)`.

## Never

- Do not call `unwrap()`, `panic!`, or `todo!` in library code on a path that user
  input can reach.
- Do not expose `anyhow::Error` in the public API of a library.
- Do not add `unsafe` to fix a borrow checker error.
- Do not hold a lock across an `.await`.
- Do not call a blocking function in an async function.
- Do not add `#[allow(clippy::...)]` without a comment that gives the reason.
- Do not connect to a network device or a network service in a test.

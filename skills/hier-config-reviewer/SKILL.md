---
name: hier-config-reviewer
description: Use when the user asks for a hier-config review, a combined review, or one consolidated set of review findings before a pull request in a hier-config or netdevops repository (Python, Rust, or Go). Also use when the user wants a verdict on the comments that a pull request already carries, a check of the changelog entry, review findings posted as pull request comments with suggested fixes, an approval or a change request on a pull request, or a map that splits a large pull request into smaller pull requests. With --handoff, returns the findings as a report for the hc-sde-qa persona and posts nothing.
license: MIT
compatibility: Needs git, the gh CLI (authenticated), and Python 3. Uses the toolchain of each detected language (Poetry or uv, cargo, go). Docker is optional (Playwright checks).
metadata:
  argument: "[PR number | branch | path] [--handoff]"
---

Measure the diff first. If the diff is large, propose a map that splits the pull
request (PR) into smaller PRs, and ask the user whether to post the map. If the map
posts, the review ends. Otherwise, run the gates and the reviews, judge the comments
that the PR already carries, check the changelog entry, merge all findings into one
prioritized list, and post the comments that the user selects to the PR.

Argument: an optional review target (a PR number, a branch, or a path). If the target
is a PR number or a branch that is not checked out, check it out first with
`gh pr checkout <number>` or `git switch <branch>`. All reviews then run against the
current branch. A path target limits the reviews to that path.

`--handoff`: optional flag. The `hc-sde-qa` persona of the `hc-sde-issue` workflow
passes it. In handoff mode, the skill does not talk to a human and does not write to
the PR:

- Step 2 measures the diff and reports the count. It does not build a split map, and
  it does not ask the split question.
- Steps 3 to 7 run as usual.
- Steps 8, 9, and 10 do not run. The skill posts no comment and sets no review state.
- The skill ends with the handoff report in "Handoff report" below.
- The skill asks the user no question at any point. If a step needs an answer, for
  example a missing issue number, record the gap in the report and continue.

Write all prose that this skill produces in ASD-STE100 Simplified Technical English
(STE). This applies to the consolidated list and to every PR comment. Do not change
code, file paths, commands, or quoted output.

This skill uses capability terms ("start a subagent", "invoke a skill", "ask a choice
question", "session temporary directory"). The file
`references/platforms.md` of the `hc-sde-issue` skill maps each term to the tools of
each platform. If that skill is not installed, use the closest tool of your platform.

## Step 1 — Detect the languages and the standards

1. Find the base branch and the changed files:

   ```bash
   BASE=$(gh pr view --json baseRefName --jq '.baseRefName' 2>/dev/null \
     || gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
   git fetch origin "$BASE" --quiet
   git diff --name-only "origin/$BASE...HEAD"
   ```

2. Detect each language of the repository and of the diff:

   | Language | Signal | Reference |
   |---|---|---|
   | Python | `pyproject.toml`, `setup.py`, or `*.py` in the diff | `references/python.md` |
   | Rust | `Cargo.toml`, or `*.rs` in the diff | `references/rust.md` |
   | Go | `go.mod`, or `*.go` in the diff | `references/go.md` |

   A language applies when the diff changes a file of that language or its build
   file. Record the absolute path of each applicable reference file. The references
   are in the folder of this skill.

3. Read the repository standards: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and
   `docs/dev/*.md` if they exist. When a repository standard and a reference item
   disagree, the repository standard wins.

4. Find an in-repo review skill. Look for `SKILL.md` files in
   `.claude/skills/*review*/`, `.agents/skills/*review*/`, and
   `.github/skills/*review*/`. Example: `hier-config-review` in `hier_config`.
   Record each path.

## Step 2 — Measure the diff and decide on a split

A large PR is hard for a human to review. This step measures the diff before any
review runs. If the diff is large, the step builds a map that shows how to split the PR
into smaller PRs, and it asks the user whether to post the map. The step proposes the
split only. It does not create an issue. It does not open a PR.

Do not start a review subagent, and do not invoke a review skill, until this step
ends.

### Step 2.1 — Measure the diff

Count the changed lines against the base branch. Exclude generated and vendored
files, because a human does not review them line by line.

```bash
git diff --numstat "origin/$BASE...HEAD" | awk '
  $1 == "-" { next }
  $3 ~ /(^|\/)(poetry\.lock|uv\.lock|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|go\.sum)$/ { next }
  $3 ~ /(^|\/)vendor\// { next }
  $3 ~ /\.(min\.js|min\.css|map|svg)$/ { next }
  $3 ~ /(_pb2\.py|\.pb\.go|_generated\.(py|rs|go))$/ { next }
  { total += $1 + $2 }
  END { print total + 0 }'
```

If the total is 500 or less, skip the rest of this step. Tell the user the measured
count, and continue with Step 3.

In handoff mode, skip the rest of this step for all totals. Record the measured count
for the handoff report, and continue with Step 3.

### Step 2.2 — Find the parent issue

1. Read an issue number from the branch name. The pattern is
   `u/<account>/<number>-<slug>`.
2. If the branch name has no number, read the PR body for `Closes #<number>`,
   `Fixes #<number>`, or `Resolves #<number>`.
3. If neither has a number, ask the user for the number with a choice question or a
   plain question.

Read the issue:

```bash
gh issue view <ISSUE> --json number,title,body,labels
```

Take the title, the body, and the acceptance criteria.

If the read fails, build the map from the PR body and the diff alone. Mark the map
with "parent issue not read". Tell the user.

### Step 2.3 — Group the diff

Group the changed files and hunks by intent. Each group maps to one requirement or one
acceptance criterion of the parent issue. Apply these rules:

1. Keep each group under about 400 non-generated lines. Split a larger group.
2. Make each group merge on its own. The build passes. The test suite passes.
3. Give each group its own tests, its documentation, and its changelog entry.
4. Put a shared helper in the earlier group that needs it.
5. Fold a group under about 30 lines into a neighbour group.
6. Keep a generated file with the change that generates it.
7. Order the groups so that a dependency comes first.

If every hunk depends on every other hunk, the change is atomic. Report that fact and
the reason. Do not force a split. Do not ask the split question. Continue with Step 3.

### Step 2.4 — Write the map

Read the GitHub account name for the branch prefix. The author of the PR cuts the new
branches, so use the account of the author, not the account that runs the review:

```bash
gh pr view --json author --jq '.author.login' || gh api user --jq '.login'
```

The map opens with the measured line count, the parent issue number, the parent
title, and the group count. The map then shows one section for each group:

- **Sub-issue title** — one imperative sentence in STE.
- **Serves** — the requirement or the acceptance criterion of the parent issue.
- **Files** — the file paths. Name the functions when one file splits across two
  groups.
- **Size** — the approximate non-generated line count.
- **Branch** — `u/<github-account>/<SUB-ISSUE>-<slug>`, where `<github-account>` is
  the account of the PR author. `<SUB-ISSUE>` stays a placeholder, because the
  sub-issue does not exist yet.
- **Order** — the merge position, and the groups that this group depends on.

End the map with a collapsed `<details>` block. The block holds the commands that
create each sub-issue, link it to the parent, and create the branch, so a later run
can execute them:

````markdown
<details>
<summary>Commands to create the sub-issues and the branches</summary>

```bash
URL=$(gh issue create --title "Add the FastIron platform enum member" --body "Part of #123.")
ID=$(gh api "repos/{owner}/{repo}/issues/${URL##*/}" --jq '.id')
gh api "repos/{owner}/{repo}/issues/123/sub_issues" -F sub_issue_id="$ID"
git switch -c "u/<github-account>/${URL##*/}-fastiron-platform-enum"
```

</details>
````

Show the full map to the user.

### Step 2.5 — Ask whether to post the map and end the review

If the target has no PR, skip this sub-step. The map stays with the user. Continue
with Step 3.

Ask the user one choice question: "Post the split map to the PR and end the review?"
Offer these options:

- "Yes, post the map and stop"
- "No, continue the full review"

Do not post the map before the user answers.

If the user selects "Yes":

1. Write the map to a file in the session temporary directory, because the map is
   long.
2. Post the file as one general PR comment:

   ```bash
   gh pr comment --body-file "$MAP_FILE"
   ```

3. Report the PR URL.
4. End the skill here. Do not run Step 3 or any later step. Do not post any other
   comment.

Do not post the map as an inline comment. Do not create the sub-issues, and do not
open the smaller PRs. The map is a proposal.

If the user selects "No", continue with Step 3. Do not ask about the map again, and do
not post the map in a later step.

## Step 3 — Run the gates and the reviews

Run each review. Collect the findings. Do not apply fixes, and do not let any review
post its own comments.

### Step 3.1 — Gates

1. If the repository documents one gate command (in `AGENTS.md`, `CLAUDE.md`,
   `CONTRIBUTING.md`, or the PR template), run it. Example for `hier_config`:
   `poetry run ./scripts/build.py lint-and-test`.
2. Else run the gates in the "Gates" section of each applicable reference file.
3. Also read `.github/workflows/`. A CI job that the gates above do not cover is a
   gap. Record it for the report. Do not run a job that publishes or deploys.

Each gate failure is a MUST FIX finding. Give the tool, the `path:line`, and the
message.

### Step 3.2 — Language standards review

For each applicable language, start one review subagent. Start them all at the same
time if the platform allows it. Give each subagent this prompt:

> Review the diff of `origin/<BASE>...HEAD` in `<repository path>` against the
> standards in `<absolute path of references/<lang>.md>`, and against the repository
> standards in `AGENTS.md` and `docs/dev/` where they exist. Review only the
> `<language>` files in the diff. Do not change files. Return a list of findings.
> Each finding has: `path:line`, the reference section, one sentence that states the
> defect, one sentence that states the required change, and the replacement lines if
> the fix replaces a few adjacent lines and has no design decision.

If the platform cannot start a subagent, do the same review in the current session,
one language at a time.

### Step 3.3 — In-repo review skill

For each in-repo review skill from Step 1, read its `SKILL.md` and follow it in report
mode. Do not apply a fix that it proposes. Do not run a step that posts to GitHub.
Collect its findings with its severity names. Map its severities to the priorities of
Step 7.

### Step 3.4 — Security review

If the `security-review` skill is available, invoke it and follow it. Otherwise,
read the diff for these defects, and report each one with a severity (critical,
high, medium, low):

- a secret, a token, or a password in code, tests, fixtures, or documentation;
- input that reaches a shell, `eval`, `exec`, a template, a regular expression, or a
  file path without validation;
- unsafe deserialization: `pickle`, `yaml.load` without a safe loader, `unsafe` in
  Rust without a `// SAFETY:` comment;
- TLS verification that is off, or a network call with no timeout;
- a new dependency that is not pinned by the lock file, or that has no maintenance.

### Step 3.5 — Code review

If the `code-review` skill is available, invoke it and follow it. Pass the review
target. Do not pass `--comment` or `--fix`. If the skill reports findings through a
findings tool, also keep the findings for the consolidated list.

If the skill is not available, read the full diff for correctness defects: wrong
logic, a missed branch, an off-by-one error, a wrong error path, a race, a resource
that does not close, and a change of public behavior with no test.

Pass a path target to each subagent in its prompt, and to each skill as its argument.
If a review does not accept a path, run it on the full diff, and drop its findings
that are outside the path.

## Step 4 — Judge the existing pull request comments

Read every comment that the PR already carries, and judge each one against the current
code. This step reports a verdict for each comment. It does not post a reply to a
comment thread.

If the review target is not a PR, skip this step, and tell the user.

If the `superpowers:receiving-code-review` skill is available, invoke it and follow
it. It sets the standard for this step: verify each claim against the code, and do not
agree without evidence.

Read the comments with `gh`:

```bash
PR=$(gh pr view --json number --jq '.number')
gh api "repos/{owner}/{repo}/pulls/$PR/comments" --paginate \
  --jq '.[] | {id, user: .user.login, path, line, in_reply_to_id, body}'
gh api "repos/{owner}/{repo}/pulls/$PR/reviews" --paginate \
  --jq '.[] | select(.body != "") | {id, user: .user.login, state, body}'
gh api "repos/{owner}/{repo}/issues/$PR/comments" --paginate \
  --jq '.[] | {id, user: .user.login, body}'
```

Skip these comments:

- A comment that an earlier run of this skill posted. Such a comment opens with a
  priority in bold, or it holds the PRAISE paragraph or the split map.
- A comment from a bot account: a login that ends with `[bot]`, for example
  `github-actions[bot]`, `renovate[bot]`, or `claude[bot]`. An automated review
  workflow posts such comments.
- A comment that asks for no change, for example a question that the author answered,
  or an approval note.

Judge each remaining comment. Read the file at the commented path and line first.
Assign one verdict:

| Verdict | Criteria |
|---|---|
| VALID | The defect exists in the current code, and the requested change is correct. |
| VALID, RESOLVED | The comment was correct, and a later commit applied the change. |
| INVALID | The current code does not hold the defect, or the claim is wrong. |
| OUT OF SCOPE | The claim is correct, but it is about code that this PR does not change. |
| UNCLEAR | The comment does not state enough for a verdict. |

Rules for a verdict:

- Judge the comment by the code only. The identity of the author does not change the
  verdict.
- Give a reason of one or two sentences. Support the reason with evidence: a
  `path:line` that shows the current code, or the commit that applied the change.
  Find that commit with `git log --oneline -S '<changed text>' -- <path>`.
- If a comment reports a defect that a review in Step 3 also found, keep one item.
  Record both sources.
- Add each VALID comment to the consolidated list in Step 7 as a finding. Assign the
  priority with the table in Step 7. Mark the item `[from PR comment by @<login>]`.
- Do not add a VALID, RESOLVED comment, an INVALID comment, or an OUT OF SCOPE comment
  to the consolidated list.
- An UNCLEAR comment becomes a CONSIDER FIXING item that asks the author for the
  missing detail.

Show a table to the user with one row for each judged comment: the comment id, the
author, `path:line`, the verdict, and the reason. Show this table before the
consolidated list.

## Step 5 — Check the changelog entry

The repositories use one of two changelog methods. Detect the method first.

### Step 5.1 — Detect the method

```bash
python3 - <<'PY'
import pathlib
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
cfg = None
for name in ("towncrier.toml", "pyproject.toml"):
    path = pathlib.Path(name)
    if path.is_file():
        cfg = tomllib.loads(path.read_text()).get("tool", {}).get("towncrier")
        if cfg is not None:
            break
if cfg is not None:
    print("towncrier")
    print(cfg.get("directory", "changes"))
    print(" ".join(t["directory"] for t in cfg.get("type", [])))
elif pathlib.Path("CHANGELOG.md").is_file():
    print("keep-a-changelog")
else:
    print("none")
PY
```

- `towncrier`: go to Step 5.2. If the type list is empty, use the towncrier default
  types: `feature`, `bugfix`, `doc`, `removal`, `misc`.
- `keep-a-changelog`: go to Step 5.3.
- `none`: the project has no changelog. Skip this step, and tell the user.

### Step 5.2 — Towncrier fragments

List the fragments that the PR adds:

```bash
git diff --name-only --diff-filter=AMR "origin/$BASE...HEAD" -- "$FRAGMENT_DIR"
```

A valid name is `<number>.<type>` or `<number>.<type>.<counter>`, where:

- `<number>` holds digits only. It is a GitHub issue number or a GitHub PR number.
- `<type>` is one of the configured types.
- `<counter>` holds digits only. It is optional. Towncrier uses it for two fragments
  of the same type and the same number.

The regular expression is `^[0-9]+\.<type>(\.[0-9]+)?$`.

These names are not valid:

| Name | Reason |
|---|---|
| `#123.fixed` | The name holds a `#`. Use `123.fixed`. |
| `+new-driver.added` | The `+` prefix makes an orphan fragment. Every fragment needs a number. |
| `new-driver.added` | The name holds a slug, not a number. |
| `u-jtdub-123-new-driver.added` | The name holds a branch name, not a number. |
| `123.feedback` | `feedback` is not a configured type. |

Go to Step 5.4.

### Step 5.3 — Keep a Changelog entry

Read the diff of `CHANGELOG.md`:

```bash
git diff "origin/$BASE...HEAD" -- CHANGELOG.md
```

A valid entry:

- is a new list item under `## [Unreleased]`, not under a released version;
- is under one of the sections `### Added`, `### Changed`, `### Deprecated`,
  `### Removed`, `### Fixed`, `### Security`, and the section matches the change;
- ends with `(#<number>)`, where `<number>` is a GitHub issue number or a GitHub PR
  number;
- describes the change for a user, not the code of the change.

### Step 5.4 — Check that the number points to real work

Collect the acceptable numbers:

```bash
gh pr view --json number,title,body --jq '.number, .title, .body'
git rev-parse --abbrev-ref HEAD
```

A number is acceptable when one of these is true:

- It is the number of this PR.
- It is the number of an issue that the PR body closes, for example `Closes #123`.
- It is the issue number in the branch name `u/<account>/<number>-<slug>`.

Confirm that the number exists with `gh issue view <number>` or `gh pr view <number>`.
If a check fails because `gh` is not authenticated, report the number as
unconfirmed. Do not report it as wrong.

### Step 5.5 — Build the findings

Add these items to the consolidated list in Step 7:

| Condition | Priority |
|---|---|
| The PR changes code or user documentation, and it adds no changelog entry | SHOULD FIX |
| A fragment name or an entry does not match the rules in Step 5.2 or Step 5.3 | SHOULD FIX |
| The name or the entry matches, but the number is not acceptable | SHOULD FIX |
| The number is acceptable but unconfirmed | CONSIDER FIXING |
| A category of change in the diff has no entry, for example a fix and a new feature with only an `Added` entry | CONSIDER FIXING |

Each finding must state the correct name or the correct entry. Example: "Rename
`changes/+new-driver.added` to `changes/123.added`, because the branch names issue
#123."

A missing entry has no line in the diff. Deliver that item through the combined
comment in Step 9. An item about a file that the PR adds or changes can post inline
on that file.

## Step 6 — Verify web UI changes with Playwright

If the diff changes a web user interface, verify it in a running application with
Playwright. A web user interface includes: HTML templates, static assets (JavaScript,
CSS), the pages of an HTTP API documentation, and documentation pages that
`mkdocs.yml` builds. If the diff has no web user interface change, skip this step.

1. Start the application or `mkdocs serve` with the documented run method. Wait
   until it answers. Read the port and the credentials from the development
   environment files. Do not hardcode credentials. If no run method exists, skip this
   step, and tell the user.
2. Write a Playwright script in the session temporary directory. The script must:
   - Open each page that the change renders.
   - Assert that the page returns no server error.
   - Record browser console errors.
   - Exercise the changed behavior: follow a changed link, submit a changed form with
     valid data, or open a changed API operation.
3. Run the script. Use the official Playwright container if the host has no
   Playwright. Convert each failure into a finding:
   - A page error, a broken interaction, or a JavaScript console error: MUST FIX.
   - A visual defect that hides information or blocks a user action: SHOULD FIX.
   - A cosmetic visual defect: CONSIDER FIXING.
   - Mark each such finding as `[verified with Playwright]`. If a finding has no file
     and line, show the page URL in place of `path:line` in the consolidated list, and
     deliver it through the combined summary comment in Step 9.

If the application cannot start, skip the verification, and tell the user which
changes did not get a functional check.

## Step 7 — Consolidate the findings

Merge the findings from Step 3, Step 4, Step 5, and Step 6 into one list. Apply these
rules:

- **Deduplicate.** Two findings are duplicates when they report the same defect at
  the same file and line. Merge duplicates into one item, record each source review on
  the item, and keep the highest priority. Two different defects on the same line stay
  separate items.
- **Assign one priority to each item.** If an item matches two rows, use the higher
  priority. A reviewer's confidence level does not change the priority. Map a security
  finding by its severity only — it does not also match the "bug" criterion: critical
  or high is MUST FIX, medium is SHOULD FIX, low is CONSIDER FIXING.

| Priority | Criteria |
|---|---|
| MUST FIX | A functional bug, a critical or high security finding, data loss, a gate failure, a test failure, or a CI failure |
| SHOULD FIX | A standards violation that can cause a problem, a missing test, a public API change with no documentation, or a medium security finding |
| CONSIDER FIXING | A style improvement, a simplification, a performance improvement, or a low security finding |
| NIT PICK | A cosmetic item: a typo, wording, whitespace, or comment phrasing |

- **Write the PRAISE section.** Read the diff for work that the PR does well.
  Examples: a thorough test, a clean simplification, a well-handled edge case, or clear
  documentation. Write one short paragraph, two to four sentences, in STE. The
  paragraph describes real work in the diff. Do not invent praise. Show this paragraph
  under a **PRAISE** heading, before the numbered list. PRAISE is not a finding: do
  not number it, and do not put it in the priority table.
- **Sort the list** by priority: MUST FIX first, then SHOULD FIX, then CONSIDER
  FIXING, then NIT PICK.
- **Number each item** across the full list (1, 2, 3, ...). The user selects items by
  these numbers in Step 8.
- **Write each item in STE.** Each item shows: the number, the priority, the file and
  line as `path:line`, one sentence that states the defect, and the source review(s).
  An item that comes from an existing PR comment also shows
  `[from PR comment by @<login>]`.
- **Mark simple fixes.** A simple fix is a change that replaces one line or a few
  adjacent lines and has no design decision. Mark these items with `[suggested fix
  available]` and prepare the replacement lines.

Show the full consolidated list to the user.

In handoff mode, go to "Handoff report" below. Do not run Step 8, Step 9, or Step 10.

## Handoff report (handoff mode only)

Return the consolidated list in this format. The `hc-sde-issue` workflow reads it, so
keep the headings exactly as shown. Put no text after the last section.

````markdown
## QA findings

Diff size: <count> non-generated lines

| # | Priority | Location | Defect | Required change | Sources |
|---|---|---|---|---|---|
| 1 | MUST FIX | path/to/file.py:42 | <one STE sentence> | <one STE sentence> | gates, code-review |

### Suggested fixes

#### 1
```suggestion
<replacement lines>
```

### Gaps

- <a review that did not run, a check that was unconfirmed, or "None">
````

Rules for the report:

- Include every item from Step 7, of all priorities. Do not drop NIT PICK items.
- Write "Required change" so that an engineer can apply it with no other context.
- Include a suggested fix only for an item marked `[suggested fix available]`.
- If the list is empty, write one table row: `| — | — | — | No findings | — | — |`.
- Do not include the PRAISE paragraph.

## Step 8 — Ask which items get comments

Ask the user which items to comment on, with a multi-select choice question. Offer
these options: "All MUST FIX items", "All MUST FIX and SHOULD FIX items", "All items",
"No comments". The user can also type specific item numbers.

In the same call, if the platform allows it, add a second question: "Post the PRAISE
comment?" with the options "Yes" and "No".

Do not ask about the split map here. Step 2 handled the map.

Do not post any comment before the user answers. If the user declines every comment,
skip Step 9.

## Step 9 — Post the comments

Use the `gh` CLI for all GitHub interactions. Find the PR for the current branch with
`gh pr view --json number,headRefOid`. The `headRefOid` value is the `commit_id` for
the API calls below. If no PR exists, stop and tell the user. Offer to show the
comments to the user instead.

Compare `git rev-parse HEAD` with `headRefOid`. If they differ, the local branch and
the PR head do not match, and the line numbers can be wrong. Stop and tell the user to
push, or to confirm that the comments target the pushed head.

If the user selected "Yes" for the PRAISE comment, post the PRAISE paragraph first as
one general PR comment with `gh pr comment`. Do not post it as an inline comment, and
do not add a suggestion block to it.

Post each selected item as an inline review comment on the changed line:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  -f body="$BODY" \
  -f commit_id="$HEAD_SHA" \
  -f path="$FILE" \
  -F line=$LINE \
  -f side=RIGHT
```

Comment rules:

- Write the comment body in STE.
- The body contains: the priority in bold, then one or two sentences that state the
  defect and the required change. Do not repeat the file path or the source review;
  the inline position shows the location.
- The PRAISE comment body contains **PRAISE** in bold, then the paragraph from
  Step 7.
- If the item has a simple fix, add a GitHub suggestion block after the prose:

  ````markdown
  **SHOULD FIX**: The model field uses a mutable `list`.

  ```suggestion
      match_rules: tuple[MatchRule, ...]
  ```
  ````

  The suggestion block replaces the commented line(s) exactly. Include only the
  replacement lines, with the exact indentation of the file. To replace more than one
  line, add `start_line` and `start_side` to the API call.
- An inline comment must target a line that the PR diff changed. Collect all findings
  that are outside the diff into one combined comment, list each as `path:line` plus
  the defect sentence, and post it once with `gh pr comment`.

After the comments post, report the count and the PR URL. Do not apply the fixes to
the working tree unless the user asks.

## Step 10 — Set the review state (only on request)

Do not set the review state of the PR. The review ends after Step 9.

Run `gh pr review --approve` or `gh pr review --request-changes` only when the user
asks for that state in an explicit instruction. A request for a review, for comments,
or for a verdict on the existing comments is not such an instruction.

If the user asks for a state, check the author first:

```bash
PR_AUTHOR=$(gh pr view --json author --jq '.author.login')
ME=$(gh api user --jq '.login')
```

If `PR_AUTHOR` and `ME` are the same, set no state. GitHub does not accept an approval
or a change request from the author of the PR. Tell the user the reason.

Write the body in STE. Keep it to two or three sentences that state the result and the
count of items by priority.

```bash
gh pr review --request-changes --body "$STATE_BODY"
```

```bash
gh pr review --approve --body "$STATE_BODY"
```

Report the state that the command set, and the PR URL. If the command fails, show the
error to the user, and do not retry with the other state.

## Common mistakes

- Do not ask a question, post a comment, or set a review state in handoff mode. Return
  the handoff report only.
- Do not build or post a split map in handoff mode.
- Do not run a review subagent or a review skill before Step 2 ends. The split
  question comes first.
- Do not continue the review after the split map posts. The skill ends at Step 2.5.
- Do not ask about the split map a second time in Step 8, and do not post the map in
  Step 9.
- Do not approve a PR, and do not request changes on a PR, unless the user asks for
  that state in an explicit instruction.
- Do not run `gh pr review` on a PR that you wrote. GitHub refuses the call.
- Do not ask the user whether to set the review state. Wait for an explicit request.
- Do not agree with an existing PR comment because of the author. Read the code at the
  commented line, and judge the claim on that evidence.
- Do not post a reply to an existing PR comment thread. This skill reports the
  verdicts only.
- Do not add a resolved PR comment, an invalid PR comment, or an out-of-scope PR
  comment to the consolidated list.
- Do not accept a towncrier fragment name that holds a slug, a branch name, a `#`, or
  the orphan prefix `+`. Every fragment needs a number.
- Do not accept a `CHANGELOG.md` entry under a released version. New entries go under
  `## [Unreleased]`.
- Do not report a changelog number as wrong when the confirmation command fails for
  lack of authentication. Report the number as unconfirmed.
- Do not apply a language reference to files of another language.
- Do not let a reference item override a repository standard in `AGENTS.md` or
  `docs/dev/`.
- Do not pass `--comment` or `--fix` to `code-review`. This skill controls the
  comments.
- Do not post comments before the user selects the items.
- Do not use `curl` against the GitHub API. Use `gh`.
- Do not put a design decision in a suggestion block. Offer prose instead.
- Do not invent praise. The PRAISE comment must describe real work in the diff.
- Do not post more than one PRAISE comment, and do not post it inline.
- Do not run the Playwright check against a production service. Use the local
  development environment only.
- Do not hardcode credentials in a Playwright script. Read them from the development
  environment files.
- Do not run a CI job that publishes or deploys.
- Do not propose a split for a diff of 500 non-generated lines or less.
- Do not count a generated file toward the 500-line threshold.
- Do not create a sub-issue or open a smaller PR in this skill. The map is a proposal.
- Do not propose a group that cannot merge on its own.
- Do not force a split on an atomic change.
- Do not derive the branch prefix from the git author name. Read the GitHub account
  of the PR author with `gh pr view --json author --jq '.author.login'`. Use
  `gh api user --jq '.login'` only when that command fails.

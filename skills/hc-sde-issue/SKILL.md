---
name: hc-sde-issue
description: Use when the user starts work on a GitHub issue of a hier-config repository with /hc-sde-issue <issue>. Runs the full software development workflow with four personas — architect, engineer, QA, and UX — from requirements to a pull request that is ready for human review.
license: MIT
compatibility: Needs git, the gh CLI (authenticated), and Python 3. Docker is optional (UX tests in a container).
metadata:
  argument: "<issue> — #123, 123, <owner>/<repo>#123, or an issue URL"
---

This skill runs one GitHub issue through the software development life cycle. The
current session is the orchestrator. The orchestrator talks to the user, keeps the
state, and moves the work between four personas:

| Persona | Agent | Model tier | Job |
|---|---|---|---|
| Software architect | `hc-sde-architect` | reasoning | Read the issue, ask questions, write the implementation plan |
| Software engineer | `hc-sde-engineer` | fast | Build the plan with TDD, simplify, open a draft PR, fix the findings |
| Quality assurance (QA) | `hc-sde-qa` | reasoning | Run `hier-config-reviewer --handoff`, send the findings to the engineer |
| User experience (UX) designer | `hc-sde-ux` | reasoning | Test the change as a user, record the evidence, finish the PR description |

Argument: the GitHub issue, in one of these forms: `#123`, `123`,
`<owner>/<repo>#123`, or `https://github.com/<owner>/<repo>/issues/123`. Call the
number `ISSUE`. If the argument has no issue number, ask the user for it.

Write all prose that this skill produces in ASD-STE100 Simplified Technical English
(STE). This applies to messages to the user, the plan, issue comments, and the PR
description. Do not change code, file paths, commands, or quoted output.

## Platform terms

This skill uses capability terms, not the tool names of one AI tool. The file
`references/platforms.md` maps each term to the tools of each supported platform.
Read it before Step 0. The terms are:

- **Start a persona** — start a subagent from the persona definition.
- **Resume a persona** — send a message to a running subagent, with its context.
- **Ask a choice question** — ask the user a question with options.
- **Invoke a skill** — load a skill by name and follow it.
- **Session temporary directory** — a directory for files of this session only.

If the platform cannot start or resume subagents, use single-session mode. See
"Single-session mode" below.

## Rules for the orchestrator

- A persona cannot talk to the user. The orchestrator asks every question and
  sends the answers back to the persona. Resume the persona to send an answer.
  Record the id of each persona when it starts.
- If the platform supports subagents, always start a persona as a subagent. Do not
  do the work of a persona in the orchestrator.
- Give each persona the absolute path of the run directory in every prompt.
- Do not make a decision for the user. If a persona returns a question, ask the user.
- Keep all work inside the scope of the GitHub issue.
- If a persona returns `STATUS: BLOCKED`, show the reason to the user and ask what
  to do.

## Single-session mode

Use this mode only if the platform cannot start subagents.

1. For each step that starts a persona, read the persona file
   `personas/<persona>.md` in the folder of this skill. Ignore its frontmatter.
2. Take the role of that persona. Follow its steps and rules exactly. Write the
   same files to `RUN_DIR`.
3. When the persona returns a status line, go back to the orchestrator role. Do
   the next orchestrator step.
4. To resume a persona, read the persona file again, and read the files that it
   wrote in `RUN_DIR`. Continue from there.

The files in `RUN_DIR` hold all the state between personas. Do not use a fact that
is not in a file or in a message of the user.

## Step 0 — Prepare the run

1. Read the issue number and, if present, the repository from the argument.
2. Run these checks:

   ```bash
   git rev-parse --show-toplevel
   git status --porcelain
   gh auth status
   gh repo view --json nameWithOwner,defaultBranchRef --jq '.nameWithOwner, .defaultBranchRef.name'
   gh api user --jq '.login'
   gh issue view <ISSUE> --json number,state,title,url
   command -v docker && docker info --format '{{.ServerVersion}}'
   ```

3. If the argument names a repository that is not the repository of the checkout,
   stop. Tell the user to run the workflow in a checkout of that repository.
4. If the working tree has changes, stop. Tell the user to commit or stash the
   changes. Do not stash them for the user.
5. If `gh` fails, stop and show the output.
6. If the issue is closed, stop. Tell the user.
7. If Docker is not available, tell the user that the UX persona cannot run
   Playwright in a container. Continue.
8. Make the run directory `<tmp>/hc-sde-<repo>-<ISSUE>/`, with the subdirectory
   `screenshots/`. `<tmp>` is the session temporary directory. `<repo>` is the
   repository name without the owner. Call this path `RUN_DIR`.

Record the repository name, the default branch, and the GitHub account. The
personas need them.

### Step 0.1 — Mark the issue in progress

1. Assign the issue to the GitHub account:

   ```bash
   gh issue edit <ISSUE> --add-assignee "<GITHUB_ACCOUNT>"
   ```

2. Make sure that the label exists. Create it only if it does not exist:

   ```bash
   gh label list --search "in progress" --json name --jq '.[].name'
   gh label create "in progress" --color FBCA04 --description "Work on this issue has started"
   ```

3. Add the label:

   ```bash
   gh issue edit <ISSUE> --add-label "in progress"
   ```

4. If a command fails, for example because the account has no write access, show
   the output to the user. Ask a choice question: continue without the status, or
   stop. Do not stop the workflow unless the user selects stop.

Use this procedure for each status change in this skill. For "in review", use the
color `0E8A16` and the description "A pull request for this issue is ready for
review".

## Step 1 — Architect: requirements and plan

Start the `hc-sde-architect` persona. The prompt contains the issue number,
`RUN_DIR`, the repository name, and the default branch.

Use the model of the reasoning tier. If the platform has a model fallback rule in
`references/platforms.md`, apply it to each start and each resume of the
architect, also in Step 2 and Step 6.

The architect returns one of these status lines at the top of its reply:

- `STATUS: QUESTIONS` — a list of questions for the user.
- `STATUS: PLAN` — a complete implementation plan in `RUN_DIR/plan.md`.
- `STATUS: BLOCKED` — a reason.

### Step 1.1 — Ask the questions

The architect writes each question with a short header and, if it can, two to four
options. It marks the option that it recommends.

1. Ask the questions that have options as choice questions. Put up to four
   questions in one call if the platform allows it. Keep the recommended option
   first.
2. Ask the open questions, which have no options, as numbered plain text. Then stop
   your turn, and wait for the user to reply.
3. Resume the architect with all answers. Quote the words of the user exactly. Do
   not summarize them.
4. Repeat until the architect returns `STATUS: PLAN`.

### Step 1.2 — Agree on the plan

The user must read the full plan before the approval question. Many terminals
collapse the output of a file read and the output of a subagent. The user cannot
see that output. For this reason:

1. Read `RUN_DIR/plan.md`.
2. Write the full plan as the text of your reply. Copy it exactly as markdown. Do not
   summarize it or shorten it. Put the path of `RUN_DIR/plan.md` above the plan.
3. Ask a choice question: "Do you approve this implementation plan? The full plan
   is above this question." Offer these options: "Approve the plan", "Change the
   plan". The user can type the changes as free text.
   - If the platform supports an option preview, give "Approve the plan" a
     preview. The preview holds the problem, the decision, the scope, and the list
     of files that change, in 20 lines or less.
4. If the user wants changes, ask for the changes if the user did not type them.
   Resume the architect with the changes. Go back to Step 1.1.
5. Repeat until the user approves. Show the full new plan each time, not only the
   changes.

Do not continue to Step 2 before the user approves the plan.

### Step 1.3 — Post the plan to the issue

The architect writes an issue version of the plan to
`RUN_DIR/issue-plan-comment.md`. The comment opens with the problem, the decision,
and the scope in plain language for a product manager. The technical detail comes
after that.

```bash
gh issue comment <ISSUE> --body-file "$RUN_DIR/issue-plan-comment.md"
```

If the command fails, show the output to the user. Continue with Step 2.

## Step 2 — Engineer: build the plan and open a draft PR

Start the `hc-sde-engineer` persona. The prompt contains the issue number,
`RUN_DIR`, the path of the approved plan, the default branch, and the GitHub
account.

The engineer opens the draft PR with the GitHub account as the assignee.

The engineer returns `STATUS: DRAFT_PR` with the PR number, the PR URL, the branch
name, and the test result. It can also return `STATUS: QUESTIONS` or
`STATUS: BLOCKED`.

If the engineer finds that the plan is wrong or incomplete, it returns
`STATUS: QUESTIONS`. Resume the architect with the question first. If the architect
cannot answer from the plan and the decisions, ask the user. Then resume the
engineer with the answer. Record each plan change in `RUN_DIR/plan-changes.md`.

## Step 3 — QA: review and fix loop

The engineer and QA go back and forth a maximum of 3 times. One round is one QA
review and one engineer fix.

For `ROUND` from 1 to 3:

1. If `ROUND` is 1, start the `hc-sde-qa` persona. Otherwise, resume it. Give it the
   issue number, `RUN_DIR`, the PR number, the plan path, and `ROUND`.
2. QA writes `RUN_DIR/qa-round-<ROUND>.md` and returns one of these:
   - `STATUS: CLEAN` — no in-scope findings.
   - `STATUS: FIX` — a list of in-scope findings for the engineer.
3. If the status is `CLEAN`, end the loop.
4. If the status is `FIX`, resume the engineer. Send the full findings file path and
   this instruction: "Fix all findings in this file. Do not change code outside the
   scope of issue #<ISSUE>." Tell the user the round number and the count of
   findings.
5. The engineer returns `STATUS: FIXED` with the list of fixes, and it pushes the
   commits.

If round 3 ends with `FIX`, the engineer applies the fixes, but QA does not review
them again. Record the fact "QA round limit reached; the round 3 fixes did not get a
QA review" in `RUN_DIR/workflow-notes.md`.

QA puts out-of-scope findings in a separate section. Do not send them to the
engineer. Collect them for the PR description in Step 5.

## Step 4 — UX: test the user experience

Start the `hc-sde-ux` persona. Give it the issue number, `RUN_DIR`, the PR number,
the plan path, and the repository name.

UX returns one of these:

- `STATUS: PASS` — the change works for a user. UX added the evidence and the user
  impact section to the PR description.
- `STATUS: NO_UI` — the change has no user-facing part, or no test environment can
  start. UX wrote the reason in the PR description.
- `STATUS: DEFECTS` — a list of user experience defects.

If the status is `DEFECTS`:

1. Show the defects to the user.
2. Ask a choice question: "What do you want to do with the UX defects?" Offer these
   options: "Send to the engineer to fix", "Mark the PR ready anyway", "Leave the PR
   in draft and stop".
3. If the user selects "Send to the engineer to fix", resume the engineer with the
   defects. Then resume UX to test again. Ask again if UX finds more defects.
4. If the user selects "Leave the PR in draft and stop", go to Step 6. Skip Step 5.

## Step 5 — Finish the PR and hand it to a human

1. Read the current PR body:

   ```bash
   gh pr view <PR> --json body --jq '.body' > "$RUN_DIR/pr-body.md"
   ```

2. Add a section `## Workflow notes` at the end of the body. It holds:
   - The count of QA rounds, and the count of fixed findings.
   - The contents of `RUN_DIR/workflow-notes.md`, if the file exists.
   - The out-of-scope QA findings, as a list of `path:line` and one sentence each.
     Write "None" if there are none.
   - The plan changes from `RUN_DIR/plan-changes.md`, if the file exists.
3. Make sure that the body has the line `Closes #<ISSUE>`. If it does not, add it
   under the summary.
4. Update the PR, and mark it ready for review:

   ```bash
   gh pr edit <PR> --body-file "$RUN_DIR/pr-body.md"
   gh pr ready <PR>
   ```

5. Make sure that the GitHub account is an assignee. If it is not, add it:

   ```bash
   gh pr edit <PR> --add-assignee "<GITHUB_ACCOUNT>"
   ```

6. Change the issue status to "in review" with the procedure of Step 0.1. Do this
   only after `gh pr ready` completes without an error:

   ```bash
   gh issue edit <ISSUE> --remove-label "in progress" --add-label "in review"
   ```

Do not request a reviewer, approve the PR, or merge the PR. The assignee is not a
reviewer. A human does the review.

## Step 6 — Retrospective

1. Resume the architect. Send the paths of the plan, the plan changes, every QA
   round file, and the UX report `RUN_DIR/ux-report.md`.
2. The architect writes `RUN_DIR/issue-retro-comment.md` with a short
   retrospective. The retrospective states what the plan got wrong, what QA found,
   what UX found, and one lesson for the next plan.
3. Show the retrospective to the user.
4. Post the retrospective to the issue:

   ```bash
   gh issue comment <ISSUE> --body-file "$RUN_DIR/issue-retro-comment.md"
   ```

5. Report to the user: the PR URL, the PR state, the issue labels, the QA round
   count, the UX status, and each item that the workflow did not complete.

If the architect cannot resume, start a new `hc-sde-architect` persona with the same
files, and tell it to write the retrospective only.

## Common mistakes

- Do not start the engineer before the user approves the plan.
- Do not ask for approval of a plan that you did not write in full in your reply. A
  file read result is not always visible to the user.
- Do not answer an architect question for the user. Ask the user.
- Do not paraphrase the answers of the user to the architect. Quote them.
- Do not run more than 3 QA rounds.
- Do not send out-of-scope QA findings to the engineer.
- Do not mark the PR ready if the user selected "Leave the PR in draft and stop".
- Do not add the "in review" label while the PR is a draft. If the PR stays in
  draft, the issue keeps the "in progress" label.
- Do not close the issue. The `Closes #<ISSUE>` line in the PR closes it when a
  human merges the PR.
- Do not stash, reset, or discard the changes of the user in Step 0.
- Do not approve, merge, or request a reviewer on the PR.

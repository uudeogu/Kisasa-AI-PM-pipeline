# Bug Fix Workflow

Features follow the full workflow — Backlog to To-Do to In Progress to Review to Done. Bugs don't. A bug that sits in a three-step evaluation process while users are affected is a bug your workflow made worse.

This is the lighter-weight path for bugs. Same principles, fewer steps.

## When to use this

Use the bug fix workflow when:
- Something that used to work no longer works
- A user reported unexpected behavior
- A test that was passing is now failing
- A deploy introduced a regression

Use the full workflow when:
- The "bug" is actually a feature request ("it works, but it should work differently")
- The fix requires significant design decisions
- You're not sure what the right behavior should be

If you're not sure which path to use, start with this one. You can always escalate to the full workflow if the fix turns out to be more complex than expected.

## The bug fix board

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Reported │──▶│  Triage  │──▶│   Fix    │──▶│  Review  │
│          │   │          │   │          │   │          │
│ Issue    │   │ Human +  │   │ Agent    │   │ Human    │
│ filed.   │   │ agent    │   │ fixes.   │   │ verifies.│
│          │   │ diagnose.│   │          │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Reported

Someone files a bug. The issue should include:
- What happened (actual behavior)
- What should have happened (expected behavior)
- Steps to reproduce (if known)
- Environment details (browser, OS, account type — whatever's relevant)

No agents here. This is just a human describing what went wrong.

### Triage

**Owner:** Developer + Evaluation Agent
**Trigger:** Developer moves issue to Triage

The evaluation agent does a focused investigation, not a full requirements review. It:

1. **Reproduces the path** — traces the described behavior through the codebase to identify where things go wrong
2. **Identifies the scope** — is this a one-line fix or does it touch multiple systems?
3. **Checks for related issues** — has this been reported before? Is it related to recent changes?
4. **Posts findings** as an issue comment: "The bug is in `[file]:[function]` — [explanation of what's going wrong]. The fix is isolated to [scope]."

The developer reads the diagnosis and decides: fix it now, or escalate to the full workflow.

**Key difference from the full workflow:** The agent is diagnosing, not evaluating requirements. It doesn't need to ask "what should this do?" because the correct behavior is already known — it used to work.

### Fix

**Owner:** Developer + Implementation Agent
**Trigger:** Developer moves issue to Fix

The implementation agent writes the fix. The scope is narrow:

1. Fix the identified bug
2. Write a regression test that would have caught this bug
3. Open a PR

That's it. No refactoring around the bug. No "while I'm here" improvements. Fix, test, PR.

The regression test is non-negotiable. A bug that gets fixed without a test is a bug that will come back. The test should:
- Reproduce the exact failure described in the issue
- Pass with the fix applied
- Fail without the fix (verify this by reverting the fix locally)

### Review

Same as the main workflow. Human reviews the PR. But for bug fixes, the reviewer also checks:
- Does the regression test actually cover the reported scenario?
- Is the fix scoped correctly? (fixing only the bug, not rewriting the module)
- Could this fix break anything else?

## Severity and speed

Not all bugs are equal. The workflow is the same, but the pace changes:

**Critical** (production down, data loss, security vulnerability)
- Skip Triage if the developer already knows the cause
- Fix immediately
- Review can be post-merge if necessary (but still happens)

**High** (feature broken for users, workaround exists but is painful)
- Normal flow, but prioritize over feature work
- Same-day triage and fix

**Medium** (annoying but not blocking, edge case)
- Normal flow, normal priority
- Gets picked up when a developer has capacity

**Low** (cosmetic, minor UX issue)
- Consider whether it's worth fixing at all
- If yes, normal flow at low priority

## What about hotfixes?

A hotfix is just a critical bug where you skip Triage. The developer already knows what's wrong (or the diagnosis is obvious from logs/alerts), goes straight to Fix, and the review happens fast — possibly as a post-merge review.

This is the one case where a human reviewer might approve after merge rather than before. That's fine. The priority is stopping the bleeding. But the review still happens — never skip it entirely.

## Escalating to the full workflow

Sometimes what looks like a bug is actually deeper. Signs you should escalate:

- The "fix" requires changing an API contract
- Multiple components need to change
- You're not sure what the correct behavior should be
- The fix introduces a design decision that the team should weigh in on

When you escalate: move the issue back to the main board's To-Do column and let the evaluation agent do a full review. Don't try to force a complex problem through the lightweight path.

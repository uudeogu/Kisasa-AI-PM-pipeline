# Evals

[testing.md](testing.md) is about testing the *product* — does the feature work? `evals.md` is about testing the *agents* — are they getting better, worse, or drifting over time?

These are different problems with different tools. A green test suite tells you the code an agent wrote is correct *today*. It tells you nothing about whether the agent that wrote it would write equally good code on a similar issue next week, or whether the agent's behavior has subtly shifted under the same prompt. Without a separate evaluation layer for the agents themselves, the framework is operating with one eye closed.

The Eval Gate is the lane that opens the second eye.

## The new lane

```
... ──▶ Review ──▶ Eval Gate ──▶ Ready ──▶ Done
              │        │
            human   automated
            review   evals
```

The Eval Gate sits **between Review and Ready**. A PR can pass mechanical review by the Code Review Agent and intent review by the human architect and still fail the Eval Gate. The gate is the workflow's regression signal for the agents themselves.

This is the lane addition the framework most needed and least had. Mechanical review catches what's wrong with this PR. Intent review catches whether this PR is worth shipping. Neither catches "the backend agent has started consistently missing auth checks over the last two weeks." Evals catch that.

## Three eval tiers

The gate runs three tiers of automated evaluation against every PR. Each tier targets a different failure mode.

### Tier 1 — Schema validation

The cheapest tier. Pure structural checks, no LLM involved.

- Does the diff parse?
- Does the project build with the diff applied?
- Does the test suite run (independent of whether it passes — does it *run*)?
- Are linters and type-checkers happy?

Tier 1 catches the dumbest failures — a malformed diff, a missing import, a syntax error the Code Review Agent let through. It is fast, cheap, and runs on every PR regardless of size or tier. There is no excuse for skipping it.

### Tier 2 — Behavioral evals

Did the agent stay inside its lane? Trajectory analysis, derived from the agent's run log.

- Did the agent touch the files the team expected for this kind of issue?
- Did it stay inside its specialty? (A backend agent should not have modified migration files unless the issue asked for it.)
- Did it avoid prohibited paths? (No frontend agent should ever touch the auth middleware.)
- Did it use tools it was supposed to, and avoid tools it shouldn't have?

Tier 2 catches scope drift. The most insidious agent failure mode isn't writing wrong code — it's writing *more* code than asked, or writing it in places it shouldn't have. Behavioral evals catch that mechanically by comparing the trajectory against expectations.

### Tier 3 — Outcome evals

The most expensive tier. Runs a regression suite of past failures and their golden diffs.

- For each historical issue in the eval set, the gate has a "golden diff" — the diff that was eventually shipped.
- The agent's new diff is scored against the golden using cosine similarity on embeddings.
- The aggregate pass rate across the eval set must be ≥ 90% for the gate to pass.

The pass-rate threshold is per-issue-class, not global. Security-critical paths require 100%. Doc tweaks can tolerate 80%. The framework defines tiers; the team tunes thresholds.

Tier 3 catches drift. If a sequence of small prompt changes degrades the backend agent's behavior on issues that worked fine three months ago, Tier 3 flags it — because today's PR scores poorly against the historical goldens. Without Tier 3, drift is invisible until a production incident.

### What about first-time issue types?

Tier 3 needs a golden to score against. The first time an issue type appears, there is no golden. Three options:

- **Skip Tier 3** for the first PR of a new issue class. Tier 1 and Tier 2 still run.
- **Bootstrap with a synthetic golden** — the team writes the diff they expected, the agent's diff is scored against it.
- **Require a human-authored golden** before the agent attempts. Slowest, safest.

The default in this framework is to skip Tier 3 for the first PR and add the shipped diff to the eval set as that issue class's first golden. The team can adopt a stricter policy for security-critical classes.

## The closed feedback loop

This is the part most teams miss. Evals are not a one-time setup — they're a permanent regression mechanism that has to be fed.

### Failed runs auto-promote

Every failed run lands in a queue of candidate evals. The trajectory is captured automatically — inputs, tools used, tokens, decisions, exit reason — so the failure is reproducible.

A human reviews the queue weekly. The worst-N failures (per a configurable cutoff) get promoted into the regression suite, along with a human-authored note about what the agent should have done instead. The agent now has one more concrete example of how *not* to fail in that situation.

### Post-mortems produce evals

This is non-negotiable. Every production post-mortem must produce **at least one new eval entry**. If a regression made it through every layer of review and broke production, the eval set didn't catch it — the eval set's job is to catch the next instance of it.

This rule is what closes the loop. Most teams treat post-mortems as forgettable retros. In this framework, post-mortems are the primary source of new evals. Incidents become permanent improvements to the agent regression suite, not just a wiki page nobody re-reads.

### Weekly worst-N review

Even on weeks with no failures and no incidents, the worst-scoring N traces from the eval runs go to a human for review. "Worst" doesn't mean failed — it means lowest similarity to the golden, even on passing runs. The pattern matters: if the agent is barely passing the same eval week after week, something has shifted.

Promoting borderline-passing traces to the eval set as new goldens keeps the bar honest as the codebase evolves. The eval set is a living document; it grows roughly in proportion to how much the team uses the framework.

## Trajectory logging

Every agent run emits a structured trace. Inputs, tools called, decisions made, tokens consumed, exit reason. Successful runs and failed runs both. **Always on.**

The reason successful runs are logged is the regression loop. Today's successful diff is tomorrow's golden. If we only log failures, we lose the ability to ask "has this agent's behavior on issues like this changed?"

The trace is also what feeds Tier 2 behavioral evals (did the agent touch the right files?) and the weekly worst-N review (what does normal look like?). Without trajectory logging, the gate has nothing to chew on except the diff itself, and the diff alone hides scope drift, tool misuse, and decision changes.

## Eval Gate behavior by issue size

The Eval Gate doesn't run all three tiers identically on every PR. It tracks the run's stakes (see [sizing-and-routing.md](sizing-and-routing.md)).

| Issue size | Tier 1 | Tier 2 | Tier 3 |
|------------|--------|--------|--------|
| 1 pt (Haiku) | Always | Skip | Skip |
| 2-3 pt (Sonnet) | Always | Always | Conditional |
| 5+ pt (Opus) | Always | Always | Always |
| Security-critical (any size) | Always | Always | Always at 100% threshold |

The reason is latency. For a 1-point Haiku run that takes 2 minutes, a 5-minute three-tier eval is heavier than the run itself. For an Opus run that took 40 minutes and touched 10 files, a 5-minute eval is cheap insurance.

The architect can force any tier to run on any PR via label. The defaults are the framework's opinion on cost-benefit; the override exists because the team's opinion always wins.

## The STOP label

Any human can apply the `STOP` label to any in-flight agent run. Within 30 seconds:

- The agent halts mid-step
- Any open PR is reverted to draft
- The partial-progress note is preserved as an issue comment
- The issue returns to To-Do for the architect to triage

This is the workflow's kill switch. It exists because the failure mode for autonomous workflows isn't "agent crashes" — it's "agent makes confidently wrong choices nobody noticed until much later." The STOP label is the explicit, fast, no-permissions-needed way to interrupt a run when something looks off, before any reviewer has formal grounds to reject it.

The STOP label is not a substitute for the Code Review Agent or the human reviewer. It's an emergency brake, not a process.

## Where eval data lives

The eval set itself lives in the codebase, in a `evals/` directory parallel to `tests/`. Versioned with the product. Reviewed in PRs. The same code review process that protects production code protects the eval set.

The reason for in-repo (over a separate eval service) is the same reason testing.md keeps tests in the codebase: if the team can't read the evals, they can't trust them. An external eval service adds a layer between the team and the regression signal — that layer eventually becomes someone else's problem to maintain, and the framework's most important feedback loop atrophies.

Trajectory logs are separate. They're append-only, retention-bound (90 days is a reasonable default), and stored wherever the team stores observability data — same place as application logs. Logs feed the eval set; logs don't *replace* the eval set.

## What evals don't do

- **Evals don't replace the Code Review Agent.** Mechanical and security review still happens before the gate. The Eval Gate runs after, on PRs that already passed mechanical review.
- **Evals don't replace human review.** The architect still reviews intent. The gate runs in parallel with — or after — human review, never instead of it.
- **Evals don't gate Tier 1 schema failures retroactively.** A PR that fails Tier 1 goes back to In Progress with a structured failure note. It doesn't sit in the gate trying to pass.
- **Evals don't catch product bugs.** Product bugs are caught by [testing.md](testing.md). Evals catch *agent* bugs — drift, scope creep, regressions in agent behavior. The two layers do not substitute for each other.

## What evals enable

- **Regressions in agent behavior become observable.** Without evals, agent quality is folklore — "the backend agent seems flakier lately." With evals, it's a number.
- **Prompt and context changes become safe.** When the team updates the context corpus or refines an agent prompt, the eval set runs against the change. A drop in pass rate is the signal to back the change out.
- **Drift across model upgrades becomes manageable.** When the underlying model is updated (Sonnet 4.6 → 4.7), the eval set runs against both. The team sees the delta before shipping.
- **Post-mortems compound.** Every incident produces a new eval. The framework's "memory" of past failures grows monotonically. The same bug doesn't ship twice.

## A worked example

Six weeks into using the framework, the team notices the backend agent has stopped writing integration tests that hit a real database — the new tests mock the DB instead. Nothing in the code is wrong. The tests pass. The Code Review Agent doesn't flag it. The architect, busy, doesn't catch it during intent review.

The Eval Gate catches it.

The team's eval set includes a historical issue: "Add inventory adjustment endpoint." Its golden diff includes an integration test that uses a containerized Postgres. The new PR for a similar issue scores 0.62 cosine similarity against that golden — well below the 0.85 threshold for backend issues. Tier 3 fails. The gate returns the PR to In Progress with a structured failure note: *"This diff diverges from the historical pattern on integration tests — the golden uses a real database, this PR uses mocks."*

The architect reads the note, recognizes the drift, traces it back to a prompt change made three weeks ago that softened the language around "real database vs. mocks." The prompt is restored. The eval set picks up the corrected behavior on the next run.

Without the gate, the drift would have lasted until a production incident caused by mock-vs-real divergence — possibly months later, with no obvious cause. The cost of the eval infrastructure paid for itself the first time it caught something.

# Workflow

The full development workflow, lane by lane. Technology agnostic — this applies whether you use Linear, Jira, or sticky notes on a wall. What matters is the rules at each stage.

```
Intake ──▶ Backlog ──▶ Evaluation ──▶ To-Do ──▶ In Progress ──▶ Review ──▶ Eval Gate ──▶ Ready ──▶ Done
  │           │             │            │            │            │            │           │         │
intake     humans       evaluation     safe     implementation  human +    automated      safe     merge
agent      only         + sizing       zone        agent        review      evals         zone      all
```

Two principles run through every lane:

1. **Safe zones between automation.** Backlog, To-Do, and Ready are lanes where no agents fire. Agents run inside Intake, Evaluation, In Progress, Review, and the Eval Gate. Humans control every transition between lanes.
2. **Work is expressed as a hierarchy.** A feature is a root issue with child issues, one per agent specialty (backend, frontend, unit tests, E2E). The hierarchy encodes dependencies — children that can't start until a sibling is done are modeled as children of that sibling.

## Intake

**Owner:** Intake Agent + PM (override)
**Trigger:** New inbound content lands on any supported channel

The Intake lane is the on-ramp. Work doesn't show up as well-written tickets — it shows up as customer calls, forwarded emails, Slack threads, NPS comments, support escalations, and voicemails. The Intake Agent normalizes any of those into something Backlog can pick up.

The agent is **search-first, not create-first.** Its default action is to append a "Call Notes" comment to an existing issue when the inbound content matches. New issues are created only when match confidence is low AND create-confidence is high. Everything in between gets parked in Triage for a human.

Every issue or comment produced by the Intake Agent includes a traceability header — `Sourced from: <channel> — <speaker or sender> (<YYYY-MM-DD>)` — so six months from now anyone can walk a merged PR backward to the customer who originally said it. PII and secrets are redacted **before** any content enters an agent prompt or trace log; this is the only non-negotiable rule in this lane.

A PM can always create an issue directly without going through Intake — the same override rule that runs through the rest of the workflow. See [intake.md](intake.md) for the full breakdown.

## Backlog

**Owner:** Humans (PM, stakeholders)
**Agents:** None

The backlog is a safe space. No agents trigger here. This is where PMs, stakeholders, and the team work through ideas, customer feedback, and priorities at their own pace.

Issues land here from:
- Intake (normalized customer calls, emails, Slack threads, NPS, support escalations)
- Direct human creation (PM bypass)
- Internal ideas and technical debt

The assumption we carry forward: by the time an issue leaves Backlog, it's already been enriched with business context — ideally drafted with help from an agent that had access to the transcripts and prior decisions. The issue doesn't need to be perfect, but it needs to be substantive enough for the Evaluation Agent to have something to work with.

There is no rush. Nothing automated is watching this column.

## Evaluation

**Owner:** Evaluation Agent + PM/Architect
**Trigger:** Human moves issue from Backlog to Evaluation

When an issue lands in Evaluation, the Evaluation Agent fires. This agent is generated from the same business and product context the team operates in (see [agent-generation.md](agent-generation.md)) — not a hand-written skill list. It reads like a senior team member, not a generic assistant.

### What the agent does

1. **Reads the issue in full** against codebase, product context, and git history
2. **Posts clarifying questions** as issue comments, tagging the right person for each question
3. **Builds the work hierarchy** — breaks the root issue into child issues, one per agent specialty, expressing dependencies through parent/child relationships
4. **Signals completion** when every question is answered and the hierarchy is in place

### The back-and-forth

The agent is patient. It does not rush. If a human takes a day to respond, the issue waits. All context stays in the ticket — not in Slack, not in a separate doc. When someone picks this work up in six months, the full conversation is right where they'd expect.

### The hierarchy

The agent assigns one specialized agent per child issue via label. Typical children for a feature:

- **Backend** — API endpoints, data model changes, business logic
- **Frontend** — UI consuming the backend contract
- **Unit/integration tests** — tests for backend behavior
- **E2E tests** — full-flow Playwright coverage

Dependencies are expressed as parent/child:

```
Root issue
└── Backend
    ├── Unit/integration tests  (can't start until backend exists)
    └── Frontend                (can't start until backend exists)
        └── E2E tests           (can't start until frontend exists)
```

The specific specialties and shape depend on your team — the principle is one agent per issue, with dependencies in the hierarchy.

### Sizing and routing happen here

Before the agent signals ready, it emits **three numbers per child issue** — story points (Fibonacci 1/2/3/5/8), ACUs (Agent Compute Units, ≈15 min each), and a token budget — plus a **confidence level** (low / medium / high) and a **routed model tier** (Haiku / Sonnet / Opus).

Children over a hard cap (>5 pts OR >4 ACUs) are auto-returned for further breakdown. No specialist agent ever runs on an oversized child. Children with low confidence become Spike issues (investigation only, no PR); medium confidence triggers a plan-first workflow; high confidence gets the standard direct-PR flow. The Router binds the routed model tier to the specialist agent — same generated prompt, different runtime target. See [sizing-and-routing.md](sizing-and-routing.md) for the rules and rationale.

### Signaling ready — with a human override

When the agent is satisfied, it posts "ready for implementation" and the issue is cleared to move to To-Do.

**The human always has an override.** An architect or PM can force the "ready" signal even if the agent is still asking questions, or can push the issue back to Backlog if it's not worth pursuing. Trusting the agent's definition of "done" is something you earn over iterations — we don't gate on it in v1. The architect can also override any of the three sizing numbers or the routed tier before the issue moves to In Progress.

## To-Do

**Owner:** Architect (human)
**Agents:** None

To-Do is a safe zone. The root issue and all of its children sit here. No code gets written. No agents run. Nothing costs tokens.

This is where the architect reviews the hierarchy the Evaluation Agent built and decides what's first. They might reshape children, adjust labels, or escalate back to Evaluation. Because nothing has fired yet, all of that is free.

## In Progress

**Owner:** Architect + assigned agent for the child being worked
**Trigger:** Architect manually moves a child issue from To-Do to In Progress

**One child at a time, by the architect.** The architect reads the hierarchy and moves the first unblocked child — typically backend — into In Progress. That kicks off the agent labeled on that child.

### Why manual sequencing in v1

An engine that watches child status and auto-promotes the next unblocked sibling is an obvious next step. We deliberately don't build it yet. The logic (when a child hits Ready, what siblings are unblocked, which moves next) is real code to write and test. In v1, the architect does that move by hand. The hierarchy already encodes the dependencies — automating the move is a UI convenience, not the hard part.

When the architect moves a child to In Progress, its labeled agent runs. The agent:

- Branches off the same feature branch used by sibling children
- Implements the scope described in that child issue only
- Opens a PR against the feature branch
- Updates the child issue when the PR is up

### No TDD for agent-driven work

We don't do test-driven development here. The feature code and the tests are separate child issues with separate agents and separate PRs. A feature child moves to Review when its PR is open and CI is green. A tests child moves to Review when its tests are written and passing.

A feature is only **Done** once its tests have passed — but it is considered ready to move along the pipeline once its own code is reviewable.

## Review

**Owner:** Human architect (primary) + Code Review Agent (first pass)
**Trigger:** PR is opened by an implementation agent

Review happens per child issue. Two things happen:

### Code Review Agent — first pass

A code review agent reads the PR and posts structured comments:

- **Must fix** — mechanical and security issues (missing auth checks, SQL injection, obviously-wrong behavior, missing tests for described behavior)
- **Consider** — suggestions worth thinking about
- **Looks good** — things done well

This agent handles **syntax confirmation** and measurable checks. It does not approve. It does not merge. It does not judge whether the code is elegant or readable.

### Human architect — intent review

Code review is an art. Readability, variable naming, elegance, whether the change makes sense for the business — these are things experienced humans evaluate. The architect reviews the PR for intent, not just correctness.

If it's not right, the PR goes back to In Progress (or back to Evaluation if the issue itself was wrong). If it is right, the architect signs off — but does not merge yet. The child issue moves to **Eval Gate**.

## Eval Gate

**Owner:** Automated eval runner + Architect (on failure)
**Trigger:** Architect signs off on a PR in Review

The Eval Gate is the workflow's regression signal for the agents themselves. A PR can pass mechanical review and intent review and still fail this gate. Three tiers run, scaled to the issue's size:

- **Tier 1 — Schema validation.** Does the diff parse? Does the project build? Does the test suite run? Cheap, fast, runs on every PR.
- **Tier 2 — Behavioral evals.** Trajectory analysis — did the agent touch the right files, stay in its specialty, avoid prohibited paths?
- **Tier 3 — Outcome evals.** Regression suite of past failures with golden diffs; the new diff is scored against the golden via cosine similarity. Aggregate pass rate must be ≥ 90% (or higher for security-critical paths).

A 1-point Haiku run gets Tier 1 only. A 5-point Opus run gets all three tiers. The depth tracks the stakes.

If the gate fails, the PR returns to In Progress with a structured failure note, and the failed trace is auto-promoted into the eval set. If the gate passes, the child issue moves to **Ready**.

The `STOP` label is the workflow's kill switch — any human can apply it at any time to halt an in-flight run, revert the PR to draft, and return the issue to To-Do. See [evals.md](evals.md) for the full eval stack, the closed feedback loop, and the post-mortem-produces-evals rule.

## Ready

**Owner:** Architect
**Agents:** None (v1) — this is a safe zone

Ready is important. A child in Ready has:

- A reviewed, mergeable PR
- A human sign-off from the architect
- A passing Eval Gate
- But **no merge yet**

We don't merge children one at a time because the feature isn't complete until all children are done. Merging a backend change before its frontend and tests exist leaves `main` in a half-built state.

So Ready accumulates. Backend lands here, then unit tests, then frontend, then E2E. Once every child of a root issue is in Ready, the root issue itself is ready to merge.

### Root auto-move (deferred automation)

When all children of a root issue reach Ready, the root issue itself moves to Ready. In v1 the architect does this by hand. Automating it is another obvious next step — the signal is a straightforward check ("are all children in Ready?") — but we're not building that yet.

### What Ready enables

Ready is also where additional gates can live without blocking the per-child flow:

- Load testing across the whole feature
- Smoke testing the full integration
- Security review
- Manual QA if the team still wants it

These are future additions. The shape of Ready — a safe lane that holds completed-but-unmerged work — is what makes them possible.

## Done

**Owner:** Architect (human)
**Trigger:** Architect moves the **root** issue from Ready to Done

Moving the root issue to Done is the merge signal. Every child PR on the feature branch is merged as a batch, the feature branch folds into `main`, and the work is complete.

Deployment to production is a separate decision, controlled by the team's release process — not by this workflow. Done means merged, not shipped.

---

## A worked example

A customer mentions on a sales call that they need CSV export from the orders page.

1. **Intake.** The call transcript is normalized by the Intake Agent. It searches the tracker, finds no matching open issue, and the create-confidence is high. It creates a new root issue in Backlog with `Sourced from: customer-call — BigCorp account (2026-05-11)` in the description and the relevant transcript quote.
2. **Backlog → Evaluation.** PM reviews and moves the issue. Evaluation Agent reads it, asks which columns should be included, confirms the existing orders API can paginate, asks if the export should be server-side-streamed or client-generated. PM answers. Agent builds children: Backend (new `/orders/export` endpoint), Backend tests (integration tests for the endpoint), Frontend (Export button + progress UI), E2E test (full flow). Each child gets sized — Backend: 3 pts / 2 ACUs / Sonnet; Backend tests: 2 pts / 1 ACU / Sonnet; Frontend: 2 pts / 1 ACU / Sonnet; E2E: 1 pt / 1 ACU / Haiku.
3. **Evaluation → To-Do.** Architect reviews the hierarchy and the sizing, looks fine.
4. **To-Do → In Progress** for Backend. Backend agent (Sonnet tier) writes the endpoint, opens a PR. Backend issue → Review.
5. Code Review Agent flags a missing auth check. Backend agent fixes it. Architect signs off. Backend → Eval Gate. Tier 1 passes (build green). Tier 2 passes (only backend files touched). Tier 3 scores 0.91 against the historical golden for "add-paginated-endpoint" issues. Gate passes. Backend → Ready.
6. Architect moves Backend tests to In Progress. Testing agent writes the tests. PR up. → Review. → Eval Gate (Tier 1 only — 1 pt). → Ready.
7. Architect moves Frontend to In Progress. Similar flow. → Ready.
8. Architect moves E2E to In Progress. → Ready.
9. All four children are in Ready. Architect moves the root issue to Ready.
10. Architect moves the root issue to Done. All four PRs merge. Feature branch folds into `main`.

The architect made six manual lane transitions. The agents did the code. Every piece of work had a human sign-off AND a passing Eval Gate before its PR was considered trustworthy. The customer's original quote is still visible on the merged feature's root issue, six months later. Nothing was merged until the whole feature was complete.

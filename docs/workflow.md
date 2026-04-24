# Workflow

The full development workflow, lane by lane. Technology agnostic — this applies whether you use Linear, Jira, or sticky notes on a wall. What matters is the rules at each stage.

```
Backlog ──▶ Evaluation ──▶ To-Do ──▶ In Progress ──▶ Review ──▶ Ready ──▶ Done
  │             │            │            │            │          │         │
humans      evaluation     safe      implementation  human +     safe    merge
only         agent         zone        agent         review      zone      all
```

Two principles run through every lane:

1. **Safe zones between automation.** Backlog, To-Do, and Ready are lanes where no agents fire. Agents run only inside Evaluation, In Progress, and part of Review. Humans control every transition between lanes.
2. **Work is expressed as a hierarchy.** A feature is a root issue with child issues, one per agent specialty (backend, frontend, unit tests, E2E). The hierarchy encodes dependencies — children that can't start until a sibling is done are modeled as children of that sibling.

## Backlog

**Owner:** Humans (PM, stakeholders)
**Agents:** None

The backlog is a safe space. No agents trigger here. This is where PMs, stakeholders, and the team work through ideas, customer feedback, and priorities at their own pace.

Issues land here from:
- Customer conversations and meeting transcripts
- Feedback portals and support channels
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

### Signaling ready — with a human override

When the agent is satisfied, it posts "ready for implementation" and the issue is cleared to move to To-Do.

**The human always has an override.** An architect or PM can force the "ready" signal even if the agent is still asking questions, or can push the issue back to Backlog if it's not worth pursuing. Trusting the agent's definition of "done" is something you earn over iterations — we don't gate on it in v1.

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

If it's not right, the PR goes back to In Progress (or back to Evaluation if the issue itself was wrong). If it is right, the architect signs off — but does not merge yet. The child issue moves to **Ready**.

## Ready

**Owner:** Architect
**Agents:** None (v1) — this is a safe zone

Ready is new and it's important. A child in Ready has:

- A reviewed, mergeable PR
- A human sign-off from the architect
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

A PM files "Add CSV export to the orders page."

1. **Backlog → Evaluation.** PM moves the issue. Evaluation Agent reads it, asks which columns should be included, confirms the existing orders API can paginate, asks if the export should be server-side-streamed or client-generated. PM answers. Agent builds children: Backend (new `/orders/export` endpoint), Backend tests (integration tests for the endpoint), Frontend (Export button + progress UI), E2E test (full flow).
2. **Evaluation → To-Do.** Architect reviews the hierarchy, looks fine.
3. **To-Do → In Progress** for Backend. Backend agent writes the endpoint, opens a PR. Backend issue → Review.
4. Code Review Agent flags a missing auth check. Backend agent fixes it. Architect signs off. Backend → Ready.
5. Architect moves Backend tests to In Progress. Testing agent writes the tests against the merged-but-unmerged endpoint. PR up. → Review. → Ready.
6. Architect moves Frontend to In Progress. Similar flow. → Ready.
7. Architect moves E2E to In Progress. → Ready.
8. All four children are in Ready. Architect moves the root issue to Ready.
9. Architect moves the root issue to Done. All four PRs merge. Feature branch folds into `main`.

The architect made six manual transitions. The agents did the code. Every piece of work had a human sign-off before its PR was considered trustworthy. Nothing was merged until the whole feature was complete.

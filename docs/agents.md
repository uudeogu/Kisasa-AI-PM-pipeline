# Agents

Agent roles in this workflow. Each agent has a specific job, specific context, and specific boundaries. They are specialists, not general-purpose assistants.

**All agents are generated from the team's business and product context.** They are not hand-written skill lists. This is the single most important thing that separates this framework from generic AI workflows — see [agent-generation.md](agent-generation.md) for why and how.

## Intake Agent

**When:** New inbound content lands on any supported channel (call, email, Slack, in-app feedback, support escalation, voicemail)
**Job:** Normalize the content, search the tracker for matches, decide between append / create / park
**Communicates via:** Issue comments (when appending) and new issue descriptions (when creating)

The Intake Agent is the workflow's on-ramp. It runs before anything else and has its own deep context:

- The product vocabulary the team uses (so "the export is slow" maps to the existing `orders-export latency` issue, not a duplicate)
- The set of channels the team accepts and their relative signal strength
- The team's open and recently-closed issues (to support dedupe and regression detection)
- PII and secret patterns specific to the team's data shape

It does **not** write code. It does **not** decide priority. It does **not** speak to the customer. It produces structured tracker artifacts — appended comments or new issues — with mandatory traceability headers (`Sourced from: <channel> — <speaker or sender> (<YYYY-MM-DD>)`).

### Interaction pattern

1. Agent receives raw inbound content (transcript, email body, Slack thread, NPS comment)
2. Agent normalizes to a canonical schema and redacts PII before any further processing
3. Agent searches the tracker for matching open and recently-closed issues
4. Agent decides: append (high match confidence), create (low match + high create confidence), or park (everything else)
5. Agent writes the resulting comment or issue, with the traceability header

See [intake.md](intake.md) for the full breakdown, including channel-specific confidence thresholds and the worked example.

### Human override

A PM can create an issue directly without going through Intake. The override exists for the same reason it exists on every other agent in this framework — the agent's bar for "ready to create" is calibrated over time, and humans need an escape valve while that trust is being earned.

## Evaluation Agent

**When:** Issue moves to Evaluation
**Job:** Interrogate the issue, build the work hierarchy, signal when ready
**Communicates via:** Issue comments and child issues

This agent has deep context on:

- The full codebase (file structure, patterns, conventions)
- The product (what it does, who uses it, how it works)
- Project history (transcripts, decisions, prior context)
- The set of implementation agents available and what each specializes in

It does **not** write code. It asks the questions a senior team member would ask before work begins, and it breaks the work into labeled child issues for the specialists.

### Interaction pattern

1. Agent reads the issue against codebase and product context
2. Agent posts clarifying questions as comments, tagging the right person per question
3. Humans respond in the issue
4. Agent may ask follow-ups
5. Agent creates child issues, one per specialist, with parent/child relationships expressing dependencies
6. Agent posts a "ready for implementation" comment when satisfied

The agent is patient. It does not rush. If a human takes a day to respond, the issue sits in Evaluation until the conversation completes.

### Building the hierarchy

The Evaluation Agent's job isn't just clarification — it also decomposes the work. For each root issue, it creates child issues labeled with one specialist each (one backend child, one frontend child, one test child, etc.). Dependencies are encoded as parent/child: if frontend can't start until backend lands, the frontend child is a child of the backend child.

The agent already understands the full set of implementation agents available — that context is baked into it at generation time — so decomposition is a decision the agent is qualified to make. The architect reviews the resulting hierarchy in To-Do and adjusts if needed.

### Sizing and routing

The Evaluation Agent also emits **three numbers per child issue** (story points, ACUs, token budget), a **confidence level** (low / medium / high), and a **routed model tier** (Haiku / Sonnet / Opus). These are written into the child issue's description in a structured block.

The Router that picks the model tier is not a separate agent — it's a deterministic function inside the Evaluation Agent's decomposition step, applied to each child's size. The same backend-specialist prompt runs on Haiku for a 1-point change and on Opus for a 5-point one; specialist and model are independent dimensions.

Children that exceed the hard cap (>5 pts OR >4 ACUs) are auto-split — the agent further decomposes them rather than emit them as-is. Low-confidence children become Spike issues with no PR; medium-confidence children require a plan-first workflow at implementation time. See [sizing-and-routing.md](sizing-and-routing.md) for the rules, the escalation ladder, and the cost-ceiling watchdog that wraps every implementation run.

### Human override

A human architect or PM can override the agent's "ready" signal at any time:

- **Force ready** — clear the issue to To-Do even if the agent is still asking questions
- **Send back** — return the issue to Backlog if the team decides not to pursue it

The agent's definition of "good" evolves as the team uses the workflow. Human override exists in v1 because that trust is earned, not assumed.

## Implementation Agents

**When:** Assigned child issue moves to In Progress
**Job:** Write the code (or tests) described by this child, open a PR
**Communicates via:** Git branches, PRs, and child issue comments

Each implementation agent is specialized and generated from the same deep context as the Evaluation Agent. Typical roster:

### Backend Agent
- Knows the API layer, data models, business logic, and existing patterns
- Scope is limited to the backend child issue
- Opens a PR against the feature branch

### Frontend Agent
- Knows the component library, design system, and state management patterns
- Builds against the backend contract that already exists on the feature branch
- Opens a PR against the same feature branch

### Unit / Integration Test Agent
- Writes backend tests for the behavior described in its child issue
- Runs in the same environment as CI — no local-only assumptions
- Separate PR from the feature it tests

### E2E Test Agent
- Writes Playwright tests covering the full feature flow
- Runs last — depends on backend and frontend being in place
- Separate PR

Specialization can be by layer (what's above) or by runtime (Python vs. Go vs. TypeScript) — the principle is one agent per child issue so each PR is focused.

### The model-tier matrix

Each implementation agent exists in **three model tiers** — Haiku, Sonnet, and Opus — with the same generated prompt and the same context corpus. The tier is selected per child issue by the Router (inside the Evaluation Agent) based on the child's size:

| Tier | Use for | Workflow shape |
|------|---------|----------------|
| Haiku | 1-point mechanical (rename, dep bump, doc tweak) | Single-shot — no separate plan step |
| Sonnet | 2-3 point scoped work (one component, one endpoint) | Explore → Plan → Implement → Verify |
| Opus | 5+ point cross-cutting work | Plan-first with extended thinking + a human checkpoint between plan and implementation |

Specialist and tier are independent. `backend-specialist-haiku`, `backend-specialist-sonnet`, and `backend-specialist-opus` are three runtime targets of the same agent definition. The escalation ladder (fail 2× → upgrade tier; fail 4× → page architect) catches misclassifications automatically.

## Code Review Agent

**When:** An implementation agent opens a PR
**Job:** First-pass review for mechanical correctness — nothing more
**Communicates via:** PR comments

The Code Review Agent sits between the implementation agents and the human reviewer. It does not approve, merge, or gate anything. It posts structured comments in three buckets:

- **Must fix** — mechanical issues that should be addressed before merge (security gaps, missing tests for described behavior, contract-breaking changes not called out in the issue)
- **Consider** — suggestions worth thinking about but not blocking (naming, edge cases, alternatives)
- **Looks good** — things done well

### What it checks

- Do the changes match what the linked issue asked for?
- Do the tests actually test the described behavior?
- Are there security issues — exposed secrets, missing auth checks, unsanitized input?
- Does the code follow existing codebase patterns?
- Are new dependencies justified?

### What it does not check

- Style and formatting — linters handle that
- Readability, elegance, variable naming
- Whether the design choice makes sense for the business
- Whether the code is code you'd be proud to ship

### Why the narrow scope

Code review is art, not science. Readability, elegance, and whether a change makes sense are things only an experienced human can evaluate. An agent reviewing for "good code" will over-index on surface features and miss the things that actually matter.

We give the agent the mechanical layer — the "syntax confirmation" and security-pattern checks — so the human reviewer isn't spending their 20 minutes catching missing null checks. The human's attention is a scarce resource. Protect it for the parts of review only a human can do.

The human reviewer always comes after this agent. Always.

## What Agents Don't Do

- **Agents don't move issues between lanes.** Humans do that.
- **Agents don't decide priority.** Humans do that.
- **Agents don't merge PRs.** The architect reviews and merges happens on the root issue transition.
- **Agents don't deploy to production.** That's a team decision.
- **Agents don't talk to each other outside of issues and PRs.** All communication is visible.

## Naming Agents

Give your agents names. It makes the workflow legible — a comment from "Bart" is clearly different from a comment from "Lisa." Pick a convention that fits your team (Simpsons characters, Greek gods, whatever). The point is identity and clarity. When a human glances at an issue and sees three different names commenting, they immediately know which role each one is playing.

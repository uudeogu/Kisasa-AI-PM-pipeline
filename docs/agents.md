# Agents

Agent roles in this workflow. Each agent has a specific job, specific context, and specific boundaries. They are specialists, not general-purpose assistants.

**All agents are generated from the team's business and product context.** They are not hand-written skill lists. This is the single most important thing that separates this framework from generic AI workflows — see [agent-generation.md](agent-generation.md) for why and how.

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

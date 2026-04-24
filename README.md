# AI PM Agents

An opinionated guide to AI-assisted product development — how to integrate AI agents into real development workflows without losing the human judgment that makes software good.

This is **not** a product you install. It's a set of opinions, patterns, and workflows for teams that want to use AI agents in their development process while keeping humans in control of the decisions that matter.

## Philosophy

**Think about how humans do it first, then make the technology match.**

The temptation with AI agents is to automate everything end-to-end. Customer feedback comes in, tickets get created, code gets written, PRs get merged — all hands-free. We believe that's the wrong approach.

Real development teams have good reasons for their workflows. An architect evaluates an issue first because context matters. A developer picks up work manually because they need to understand it before committing. Backend gets built before frontend because the contract needs to be stable. These aren't inefficiencies to optimize away — they're the practices that prevent expensive mistakes.

Our approach: **more human touchpoints, less automation. Just because we can automate doesn't mean we should.**

## The Workflow

```
Backlog ──▶ Evaluation ──▶ To-Do ──▶ In Progress ──▶ Review ──▶ Ready ──▶ Done
  │             │            │            │            │          │         │
humans      evaluation     safe      implementation  human +     safe    merge
only         agent         zone        agent         review      zone      all
```

Seven lanes. Three of them (Backlog, To-Do, Ready) are safe zones where no agents fire. The other three wrap agents around human-gated transitions. A feature is decomposed into a parent issue with child issues, one per specialist agent (backend, frontend, unit tests, E2E). The architect sequences children through the lanes by hand in v1 — obvious automation is deferred, not skipped.

See [docs/workflow.md](docs/workflow.md) for the full breakdown.

## What's Here

| Document | What it covers |
|----------|---------------|
| [docs/workflow.md](docs/workflow.md) | The full workflow from Backlog to Done, lane by lane |
| [docs/agents.md](docs/agents.md) | Agent roles, responsibilities, boundaries |
| [docs/agent-generation.md](docs/agent-generation.md) | Why agents are generated from business context, not hand-written |
| [docs/opinions.md](docs/opinions.md) | Every opinionated decision we made and why |
| [docs/prompts.md](docs/prompts.md) | Agent prompt templates — the shape a generated agent should take |
| [docs/testing.md](docs/testing.md) | Testing strategy — unit, integration, and E2E with Playwright |
| [docs/bugfix.md](docs/bugfix.md) | Bug fix workflow — lighter-weight path for bugs vs. features |
| [docs/architecture.md](docs/architecture.md) | Technical architecture and integration patterns |

## Who This Is For

Teams that want to use AI coding agents but are wary of fully autonomous workflows. Teams that believe the right amount of automation is less than the maximum possible. Teams that want opinions backed by reasoning, not just "best practices."

---

Built by [Kisasa](https://kisasa.io)

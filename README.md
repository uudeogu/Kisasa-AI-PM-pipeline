# Kisasa AI PM Pipeline

An opinionated guide to AI-assisted product development — how to integrate AI agents into real development workflows without losing the human judgment that makes software good.

This is **not** a product you install. It's a set of opinions, patterns, and workflows for teams that want to use AI agents in their development process while keeping humans in control of the decisions that matter.

## Philosophy

**Think about how humans do it first, then make the technology match.**

The temptation with AI agents is to automate everything end-to-end. Customer feedback comes in, tickets get created, code gets written, PRs get merged — all hands-free. We believe that's the wrong approach.

Real development teams have good reasons for their workflows. A developer picks up a ticket manually because they need to understand it first. A PM answers clarifying questions because context matters. Backend gets built before frontend because the contract needs to be stable. These aren't inefficiencies to optimize away — they're the practices that prevent expensive mistakes.

Our approach: **more human touchpoints, less automation. Just because we can automate doesn't mean we should.**

## The Workflow

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Backlog  │──▶│  To-Do   │──▶│   In     │──▶│  Review  │──▶│   Done   │
│          │   │          │   │ Progress │   │          │   │          │
│ Safe     │   │ Agent    │   │ Agent    │   │ Human    │   │          │
│ space.   │   │ evaluates│   │ builds.  │   │ verifies.│   │          │
│ No agents│   │ & asks   │   │ Human    │   │          │   │          │
│ here.    │   │ questions.│  │ triggered│   │          │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

See [docs/workflow.md](docs/workflow.md) for the full breakdown.

## What's Here

| Document | What it covers |
|----------|---------------|
| [docs/workflow.md](docs/workflow.md) | The full workflow from Backlog to Done, with each column's rules |
| [docs/agents.md](docs/agents.md) | Agent roles, responsibilities, and how they interact with humans |
| [docs/opinions.md](docs/opinions.md) | Every opinionated decision we made and why |
| [docs/testing.md](docs/testing.md) | Testing strategy — unit, integration, and E2E with Playwright |
| [docs/architecture.md](docs/architecture.md) | Technical architecture and integration patterns |

## Who This Is For

Teams that want to use AI coding agents but are wary of fully autonomous workflows. Teams that believe the right amount of automation is less than the maximum possible. Teams that want opinions backed by reasoning, not just "best practices."

---

Built by [Kisasa](https://kisasa.io)

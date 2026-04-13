# Agents

Agent roles in this workflow. Each agent has a specific job, specific context, and specific boundaries. They are not general-purpose assistants — they are specialists.

## Evaluation Agent

**When:** Issue moves to To-Do
**Job:** Read the issue, identify gaps, ask clarifying questions
**Communicates via:** Issue comments

This agent has deep context on:
- The full codebase (file structure, patterns, conventions)
- The product (what it does, who uses it, how it works)
- Project history (transcripts, decisions, prior context)

It does **not** write code. It reads the issue and asks the questions that a senior developer would ask before starting work. Its goal is to make sure the issue is unambiguous and implementable before anyone writes a line of code.

### Interaction pattern

1. Agent reads the issue
2. Agent posts questions as comments, tagging the relevant person
3. Human responds in comments
4. Agent may ask follow-ups
5. When satisfied, agent posts a "ready" signal

The agent is patient. It doesn't rush. If the human takes a day to respond, that's fine. The issue stays in To-Do until the conversation is complete.

## Implementation Agents

**When:** Issue moves to In Progress
**Job:** Write the code, create the PR
**Communicates via:** Git (branches, PRs, code)

These are the agents that actually build. Each one is specialized:

### Backend Agent
- Knows the API layer, data models, business logic
- Follows existing patterns in the codebase
- Creates focused PRs that do one thing well

### Frontend Agent
- Knows the component library and design system
- Builds UI that matches existing patterns
- Only starts after the backend contract is stable

### Testing Agent
- Writes integration tests for backend changes
- Writes Playwright E2E tests for frontend flows
- Runs in the same environment as CI (no local-only assumptions)

## Code Review Agent

**When:** PR is created and CI passes, before human review
**Job:** First-pass review — catch mechanical issues so the human reviewer can focus on intent
**Communicates via:** PR comments

This agent sits between the implementation agents and the human reviewer. It doesn't approve or merge anything. It reviews the PR and posts comments categorized as:

- **Must fix** — Issues that should be addressed before merge (security gaps, missing tests for new behavior, breaking changes to existing contracts)
- **Consider** — Suggestions worth thinking about but not blocking (naming, potential edge cases, alternative approaches)
- **Looks good** — Things done well (yes, calling out good work matters)

### What it checks

- Do the changes match what the linked issue asked for?
- Do the tests actually test the described behavior, or are they just testing that the code runs?
- Are there security issues? (exposed secrets, missing auth checks, unsanitized input)
- Does the code follow existing codebase patterns?
- Are there new dependencies, and are they justified?

### What it doesn't check

- Style and formatting — linters handle that
- Minor preferences — if the code works and follows patterns, don't nitpick
- Performance micro-optimizations — unless there's an obvious problem like a query in a loop

### Why this exists

Human review is non-negotiable. But human attention is limited. If a reviewer spends 20 minutes catching a missing null check, an unused import, and a test that doesn't assert anything meaningful, they have less energy for the question that actually matters: "does this change make sense?"

The code review agent handles the first category so the human can focus on the second.

### What it is not

It is not the final reviewer. It is not a gate. A human always reviews after it. If the agent isn't sure about something, it says so rather than pretending to have an opinion.

See [docs/prompts.md](prompts.md) for the full prompt template.

## What Agents Don't Do

- **Agents don't move issues between columns.** Humans do that.
- **Agents don't decide priority.** Humans do that.
- **Agents don't merge PRs.** Humans review and merge.
- **Agents don't deploy to production.** That's a team decision.
- **Agents don't talk to each other outside of the issue.** All communication is visible in the issue or PR.

## Naming Agents

Give your agents names. It makes the workflow legible. When a comment shows up from "Bart" instead of "AI Assistant," the team immediately knows which agent is talking and what its role is. Pick a naming convention that works for your team — Simpsons characters, Greek gods, whatever. The point is identity and clarity.

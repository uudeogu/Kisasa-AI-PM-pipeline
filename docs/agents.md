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

## What Agents Don't Do

- **Agents don't move issues between columns.** Humans do that.
- **Agents don't decide priority.** Humans do that.
- **Agents don't merge PRs.** Humans review and merge.
- **Agents don't deploy to production.** That's a team decision.
- **Agents don't talk to each other outside of the issue.** All communication is visible in the issue or PR.

## Naming Agents

Give your agents names. It makes the workflow legible. When a comment shows up from "Bart" instead of "AI Assistant," the team immediately knows which agent is talking and what its role is. Pick a naming convention that works for your team — Simpsons characters, Greek gods, whatever. The point is identity and clarity.

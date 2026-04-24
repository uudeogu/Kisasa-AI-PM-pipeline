# Architecture

How the pieces connect technically. This is intentionally high-level — the specifics depend on your stack and tools.

## The trigger chain

```
Issue Tracker (webhook)
       │
       ▼
Serverless Function (e.g., Vercel, Lambda)
       │
       ├── Validates: Is this an issue update?
       ├── Validates: Did the lane change?
       └── Validates: Is this a lane that triggers an agent?
               │
               ▼
       GitHub Dispatch Event
               │
               ▼
       GitHub Actions Workflow
               │
               ├── Sets up MCP server
               ├── Sets up Claude Code
               └── Kicks off the right agent for the lane
```

### Which lanes trigger agents

Only three of the seven lanes kick off agents:

| Lane | Agent | Trigger condition |
|------|-------|-------------------|
| Evaluation | Evaluation Agent | Root issue enters Evaluation |
| In Progress | Specialist implementation agent | Child issue enters In Progress (agent is determined by the label the Evaluation Agent assigned) |
| Review | Code Review Agent | PR is opened from a feature branch |

The other four — Backlog, To-Do, Ready, Done — are safe zones. A transition into one of them does not fire anything. The webhook filter rejects them before a dispatch event is created.

### Step by step

1. **Webhook from issue tracker** — When an issue changes (lane move, label change, assignment), the tracker sends a webhook payload to a serverless function.

2. **Serverless function filters and routes** — Not every change matters. The function checks: Is this an issue update (not a comment)? Did the lane change? Is the new lane one that triggers an agent? If all conditions pass, it creates a GitHub dispatch event.

3. **GitHub Actions picks up the dispatch** — A workflow is triggered with the issue details as inputs. The workflow sets up the environment: MCP server for tool access, Claude Code for the agent runtime.

4. **Agent runs** — The agent for that lane (evaluation, the labeled specialist, or code review) runs with full context of the issue, its parent/children, and the codebase.

### Human override on the Evaluation Agent

When the Evaluation Agent posts its "ready" signal, the default path is for a human to move the issue from Evaluation to To-Do. A human can also force the issue to To-Do before the agent has posted ready — this is the override. Implementation: the architect either adds a label the filter accepts, or manually changes the lane in the tracker. Either way, the architect's move is the trigger, not the agent's signal.

### Deferred automation — root auto-move and batched merge

Two transitions are manual in v1 that are obvious candidates for automation:

- **All children Ready → root Ready.** When every child of a root issue has moved to Ready, the root should follow. The signal is a straightforward derived check ("are all children of this root in Ready?"). In v1 the architect runs that check in their head and moves the root by hand. Automating it is a small serverless function watching the Ready-lane webhook.

- **Root Ready → Done triggers batched merge.** The architect moves the root to Done when the feature is ready to ship. In v1 this is also the signal for the architect to merge every child PR on the feature branch. Automating the merge — when the root transitions to Done, merge every PR associated with its children — is the other obvious next step.

Both are deferred so v1 can focus on the agents and the context generation, not on orchestration code.

## Context is everything

The most important architectural decision is **how much context the agents have**. An agent without context asks bad questions and writes bad code.

### Product context
- Meeting transcripts from stakeholder conversations
- Product briefs and requirement documents
- Prior decisions and their reasoning

This lives in a Claude project (or equivalent). Every chat in that project has access to all of this context. When the agent evaluates an issue, it's not starting from zero — it knows what the product is, who uses it, and what decisions have already been made.

### Code context
- Full codebase access via MCP
- File structure, patterns, conventions
- Existing tests and their coverage

### Issue context
- The issue description
- All comments (including the clarification conversation)
- Related issues and their status
- Labels, assignees, priority

## What you need to wire up

| Component | Purpose | Examples |
|-----------|---------|----------|
| Issue tracker | Where issues live and move between columns | Linear, Jira, GitHub Issues |
| Webhook receiver | Catches issue changes and filters them | Vercel function, AWS Lambda, Cloudflare Worker |
| CI/CD platform | Runs agents and tests | GitHub Actions |
| Agent runtime | Executes the AI agent | Claude Code |
| Tool access | Lets agents read code and interact with services | MCP servers |
| E2E test framework | Validates user-facing behavior | Playwright |

## What you don't need

- A database for this workflow (the issue tracker is your database)
- A custom frontend (the issue tracker and PRs are your interface)
- A message queue (webhooks + dispatch events are sufficient)
- Agent-to-agent communication (agents talk through issues and PRs, not to each other)

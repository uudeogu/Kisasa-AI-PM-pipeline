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
       ├── Validates: Is an agent assigned?
       └── Validates: Did the column change?
               │
               ▼
       GitHub Dispatch Event
               │
               ▼
       GitHub Actions Workflow
               │
               ├── Sets up MCP server
               ├── Sets up Claude Code
               └── Kicks off the assigned agent
```

### Step by step

1. **Webhook from issue tracker** — When an issue changes (column move, label change, assignment), the tracker sends a webhook payload to a serverless function.

2. **Serverless function filters and routes** — Not every change matters. The function checks: Is this an issue (not a comment or label-only change)? Did the column change? Is an agent assigned? If all conditions pass, it creates a GitHub dispatch event.

3. **GitHub Actions picks up the dispatch** — A workflow is triggered with the issue details as inputs. The workflow sets up the environment: MCP server for tool access, Claude Code for the agent runtime.

4. **Agent runs** — The assigned agent (evaluation or implementation) runs with full context of the issue and the codebase.

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

# Architecture

How the pieces connect technically. This is intentionally high-level — the specifics depend on your stack and tools.

## The trigger chain

There are two entry points into the system — an **intake trigger chain** (inbound content from external channels) and a **tracker trigger chain** (lane changes inside the issue tracker). Both terminate in the same GitHub Actions runtime.

### Intake trigger chain

```
Channel adapters
  (call transcript service, email mailbox,
   Slack app, NPS webhook, support escalation,
   voicemail-to-text)
       │
       ▼
Intake webhook receiver (serverless)
       │
       ├── Normalizes payload to canonical schema
       ├── Redacts PII and secrets BEFORE anything is logged or prompted
       └── Enqueues for the Intake Agent
               │
               ▼
       GitHub Dispatch Event (intake-agent run)
               │
               ▼
       GitHub Actions Workflow → Intake Agent
               │
               └── Searches tracker, decides append / create / park
```

PII redaction happens at the serverless layer, **before** the content is enqueued. By the time the Intake Agent prompt is constructed, the content is already redacted. Once redacted content has entered an LLM prompt, the redaction has to be permanent — there is no "un-redact later" pattern that is safe.

### Tracker trigger chain

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
               ├── Sets up Claude Code at the routed model tier
               └── Kicks off the right agent for the lane
```

### Which lanes trigger agents

Five lanes kick off agents; four are safe zones:

| Lane | Agent(s) | Trigger condition |
|------|----------|-------------------|
| Intake | Intake Agent | New content lands via a channel adapter (not an issue-tracker event) |
| Evaluation | Evaluation Agent | Root issue enters Evaluation |
| In Progress | Specialist implementation agent at the routed tier | Child issue enters In Progress (specialist is set by label; tier is read from the sizing block in the issue description) |
| Review | Code Review Agent | PR is opened from a feature branch |
| Eval Gate | Automated eval runner | Architect sign-off label is applied to a PR in Review |

The other four — Backlog, To-Do, Ready, Done — are safe zones. A transition into one of them does not fire anything. The webhook filter rejects them before a dispatch event is created.

### Step by step

1. **Webhook from issue tracker** — When an issue changes (lane move, label change, assignment), the tracker sends a webhook payload to a serverless function.

2. **Serverless function filters and routes** — Not every change matters. The function checks: Is this an issue update (not a comment)? Did the lane change? Is the new lane one that triggers an agent? If all conditions pass, it creates a GitHub dispatch event.

3. **GitHub Actions picks up the dispatch** — A workflow is triggered with the issue details as inputs. The workflow sets up the environment: MCP server for tool access, Claude Code for the agent runtime.

4. **Agent runs** — The agent for that lane (evaluation, the labeled specialist, or code review) runs with full context of the issue, its parent/children, and the codebase.

### Human override on the Evaluation Agent

When the Evaluation Agent posts its "ready" signal, the default path is for a human to move the issue from Evaluation to To-Do. A human can also force the issue to To-Do before the agent has posted ready — this is the override. Implementation: the architect either adds a label the filter accepts, or manually changes the lane in the tracker. Either way, the architect's move is the trigger, not the agent's signal.

### Runtime safety signals

Two signals run alongside the trigger chain. Both can interrupt an in-flight agent run without going through the lane-change webhook path:

- **STOP label** — Any human can apply a `STOP` label on an issue or PR. The serverless filter watches for this label specifically and emits a halt event to the active GitHub Actions run, which terminates the agent within 30 seconds, reverts any open PR to draft, and preserves a partial-progress note as an issue comment. See [evals.md](evals.md).
- **Cost-ceiling watchdog** — The agent runtime tracks token consumption against the issue's budgeted ceiling. At 2× budget without a PR, the runtime pauses the agent, posts a structured summary comment, and waits for the architect to choose continue / split / kill. See [sizing-and-routing.md](sizing-and-routing.md).

These are out-of-band from the lane-change webhook path because lane changes happen only on transitions, but a runaway agent may be stuck mid-lane. The safety signals catch failures that don't naturally surface as a lane transition.

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
| Channel adapters | Feed inbound content into the Intake webhook | Otter / Fireflies (calls), Postmark (email), Slack app, Zendesk → webhook |
| Intake webhook receiver | Normalizes inbound content, redacts PII, dispatches the Intake Agent | Vercel function, AWS Lambda, Cloudflare Worker |
| Tracker webhook receiver | Catches issue / PR / label changes and filters them | Same serverless platform |
| CI/CD platform | Runs agents and tests | GitHub Actions |
| Agent runtime | Executes the AI agent at the routed model tier | Claude Code with model selection per dispatch |
| Tool access | Lets agents read code and interact with services | MCP servers |
| Trajectory logging | Captures inputs, tools, tokens, decisions for every agent run | LangSmith, Braintrust, or an append-only object store |
| Eval runner | Executes the three-tier Eval Gate on signed-off PRs | GitHub Actions workflow with the in-repo `evals/` directory |
| E2E test framework | Validates user-facing behavior | Playwright |

## What you don't need

- A database for this workflow (the issue tracker is your database)
- A custom frontend (the issue tracker and PRs are your interface)
- A message queue (webhooks + dispatch events are sufficient)
- Agent-to-agent communication (agents talk through issues and PRs, not to each other)

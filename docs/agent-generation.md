# Agent Generation

Agents in this workflow are **generated from the team's business and product context.** They are not hand-written skill lists, and the difference matters more than any other decision in this framework.

## The amateur path

The common way teams build "an AI agent" today:

1. Open a text editor
2. Write a few paragraphs describing the agent's job
3. List some technical skills ("knows TypeScript, knows React, follows our style guide")
4. Paste in a link to a style guide
5. Ship it

The result is an agent that has generic software-engineering knowledge and a vague understanding of a single team's preferences. It will write code that compiles. It will follow most of the patterns. It will still feel like a stranger.

## The path we use

The generation input is a **large body of business and product context** — the same material a new senior hire would study in their first month. Meeting transcripts. Product briefs. Customer research. Decisions and their reasoning. The codebase itself. Prior incident post-mortems. Whatever captures the company's point of view.

From that corpus, an orchestrator prompt generates each agent — Evaluation Agent, Backend Agent, Frontend Agent, and so on — with business context **embedded in the agent itself**, not bolted on as a reference link.

## Why this matters

Think about how humans do this. The person qualified to evaluate an issue isn't qualified because they know software development in the abstract — they're qualified because they've been at the company long enough to understand:

- What the product is trying to be
- Who the customers are and how they actually use it
- The company's constraints (regulatory, operational, cultural)
- The decisions already made and why they were made
- The systems that exist and why they look the way they do

A hand-written agent has none of that. It has surface knowledge. It gives surface answers. When it encounters ambiguity — which happens on every non-trivial issue — it defaults to generic best practice instead of what the team would actually decide.

A generated agent, built from real business context, reads an issue the way a senior team member reads it: through the lens of everything that context implies about how the team wants work done.

## What the context looks like

There's no fixed list. Teams assemble from what they have:

- **Meeting transcripts** — customer calls, stakeholder conversations, internal design reviews
- **Product docs** — briefs, PRDs, roadmaps, spec documents
- **Prior decisions** — RFCs, ADRs, post-mortems, "we chose X over Y because…" notes
- **Codebase** — patterns, conventions, the way things are actually done here
- **Git history** — what changed, why, how often, whose judgment shaped it
- **Team communication** — engineering channel threads where design got argued out

More is better, as long as it's real. Generic best-practice articles don't add much. The team's actual voice is what does.

## What gets generated

For each agent role, the output includes:

- The agent's purpose, written in language that reflects the team's actual vocabulary
- The boundaries of the role — what it owns and what it hands off
- Concrete patterns drawn from the codebase, not described in prose
- The team's "what not to do" rules, pulled from real past mistakes
- The voice the agent should use when commenting on issues or PRs

The agent's prompt ends up longer than a hand-written one, but only because it's carrying real context. None of it is filler.

## Regeneration, not hand-patching

When the team learns something new — a new product direction, a new pattern, a new "we got burned by this, let's not do it again" — the fix is to update the context corpus and regenerate the agents. Hand-patching individual agent prompts creates drift between what each agent knows and what the team currently believes.

## A warning

This step is where most teams cut corners. Writing a skill list is fast and feels productive. Assembling a real business-context corpus takes work — the kind of work that looks like doing nothing for a week. Teams skip it because it's hard, not because it's unnecessary.

The output of a generated agent is only as good as the context it was generated from. A thin corpus produces a thin agent. A rich corpus produces an agent that reads like a team member. There's no shortcut, and treating this step as optional is the single fastest way to end up with an "AI workflow" that doesn't actually improve anything.

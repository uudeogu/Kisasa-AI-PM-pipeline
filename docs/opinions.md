# Opinions

Every decision in this workflow is opinionated. Here's what we chose and why.

## "Just because we can automate doesn't mean we should"

AI agents can do a lot. They can create issues from customer feedback, write code, run tests, merge PRs, and deploy — all without a human touching anything. We deliberately chose not to do that.

**Why:** Fully autonomous pipelines optimize for speed at the cost of judgment. When something goes wrong (and it will), you need a human who understood the context at each step. More importantly, the intermediate human decisions — which issue to pick up next, whether the hierarchy looks right, whether this PR actually makes sense — are where the real quality comes from.

## An Intake lane exists in front of the Backlog

Work doesn't arrive as well-written tickets. It arrives as customer calls, emails, Slack threads, NPS comments, support escalations, and voicemails. The Intake lane is the safe zone that normalizes those into something the rest of the workflow can pick up. See [intake.md](intake.md).

**Why:** Without a formal Intake lane, one of two things happens. Either the PM hand-transcribes everything from memory and the framework starts from a thin issue. Or work bypasses the framework entirely — somebody pings the engineer, the engineer fixes it, no issue, no trace. Both fail in the same way: the workflow's first lane only sees a subset of what's actually moving through the team. Intake closes that gap with a search-first agent that defaults to appending to existing issues, creates new ones only above a confidence threshold, and redacts PII before any content enters an agent prompt.

## Safe zones between every automated stage

Backlog, To-Do, and Ready are lanes where no agents fire. Evaluation, In Progress, and Review are lanes where they do. Every automated stage has a safe zone before and after it.

**Why:** Full automation is a recipe for disaster. But constant human-in-the-loop checks everywhere are death by meetings. The middle ground is safe zones — places where an issue can sit without costing tokens, without consuming time, without kicking off anything. That gives humans room to reshape, escalate, or cancel without racing against automation they didn't start.

## Agents are generated from business context, not hand-written

Writing an agent prompt by hand — listing skills, describing tone, linking to a style guide — is the amateur path. It produces agents with surface knowledge and generic defaults.

**Why:** The thing that makes a senior team member qualified to evaluate work isn't generic engineering knowledge. It's that they've absorbed the product, the customers, the decisions already made, the systems that exist. An agent that hasn't absorbed that context will default to generic best practice exactly when judgment is needed. See [agent-generation.md](agent-generation.md) for the full argument.

## Evaluation is its own lane, not part of To-Do

A lot of workflows fold "evaluation" into "backlog grooming" or "to-do." We split it out.

**Why:** Evaluation is where an agent is actively doing work — reading the issue, asking questions, building the hierarchy. That's different in kind from a safe zone where nothing is happening. Making it a separate lane makes the cost and the state visible: if an issue sits in Evaluation for three days, that's information about the issue's clarity. If it sits in a folded-in "to-do," that signal is lost.

## The Evaluation Agent builds the work hierarchy

Decomposing a feature into backend/frontend/tests children is a real decision. We ask the Evaluation Agent to make it.

**Why:** The list of specialties is finite and known in advance (the agents we have defined). The dependency rules are simple (frontend blocks on backend, E2E blocks on both). A well-generated Evaluation Agent already has context on every specialist agent available. It's qualified to make this call, and handing the decomposition to the architect for every issue is work the agent should be absorbing. The architect still reviews the hierarchy in To-Do — they just don't build it from scratch.

## Three numbers per issue: story points, ACUs, and token budget

Every child issue gets sized with three numbers, not one. Story points capture complexity and risk. ACUs (Agent Compute Units, ≈15 min each) capture expected agent time. Token budget captures cost ceiling. See [sizing-and-routing.md](sizing-and-routing.md).

**Why:** A 2-line dependency bump and a 600-line cross-cutting refactor look identical to the orchestrator unless we size them. One number isn't enough — story points alone don't predict whether an agent can finish, and time-or-cost alone doesn't predict complexity or risk. The three numbers together give the framework what it needs to enforce a hard split rule (>5 pts OR >4 ACUs returns to Evaluation), pick the right model tier, and trigger the cost-ceiling watchdog when an agent grinds past 2× its budget.

## Model routing by size, not by specialty

Each specialist agent exists in three model tiers — Haiku, Sonnet, Opus — and the Router picks the tier based on the issue's size, not the specialty. The same backend-specialist prompt runs on Haiku for a 1-point rename and on Opus for a 5-point cross-cutting change.

**Why:** This is the single largest cost lever in the framework. Industry data puts well-tuned model routing at 50-80% cost reduction with no measurable quality loss on small tasks. The mistake most teams make is binding a specialist to a single model — Haiku-only loses on hard problems, Opus-only burns money on trivial ones. Specialist and model are a 2D matrix; you pick both, independently, per child issue. The escalation ladder (fail 2× → upgrade tier; fail 4× → page the architect) means misclassifications self-correct without human-in-the-loop overhead until the agents have lost twice.

## One agent per child issue

Each child issue gets exactly one specialist agent. Backend issues get the backend agent. Tests get the test agent. Not both on one issue.

**Why:** Multi-agent single-issue gets ambiguous fast. Who opens the PR? Whose comments do humans respond to? One agent per child keeps the communication model clear — one PR per child, one voice per comment thread, one owner per scope.

## Parent/child hierarchy expresses dependencies, not a todo list

The hierarchy in the issue tracker isn't just "here's a list of subtasks." Children encode "this can't start until the parent is done." Frontend is a child of backend because frontend blocks on backend. E2E is a child of frontend because E2E blocks on frontend.

**Why:** Most issue trackers already support parent/child. Using it to express dependencies means the automation signal is "when this child is Ready, siblings that depended on it are unblocked" — a concrete, derivable rule. No custom dependency-graph data model required.

## Manual architect sequencing in v1

The architect moves children from To-Do to In Progress one at a time, watching for each child to hit Ready before promoting siblings. Automating this is obvious — the dependency rules are in the hierarchy — but we don't build it yet.

**Why:** The code to watch status changes, evaluate the hierarchy, and promote siblings is real code. It needs tests, error handling, and thought about race conditions. In v1 that's time not spent on the parts of the framework that actually matter — the agents themselves, the context generation, the opinions. Manual architect moves get us the whole flow with zero integration code. The automation is the next step, not this step.

## A Ready lane exists between Review and Done

A child PR that's been reviewed is not the same as a child PR that's ready to merge. Reviewed means "looks good." Ready to merge means "all its siblings are also reviewed, and merging now won't leave `main` half-built."

**Why:** If you merge each child as it passes review, `main` briefly holds a backend change without the frontend that uses it. Tests are out of sync. Deploys are dangerous. Batching the merge — hold every child in Ready until the whole feature is ready — keeps `main` in a coherent state at every commit. Ready is also where future gates (load testing, smoke tests, security review) can live without blocking per-child review.

## An Eval Gate sits between Review and Ready

A PR that has passed mechanical review by the Code Review Agent and intent review by the human architect still goes through one more gate before reaching Ready — an automated three-tier eval (schema validation, behavioral evals, outcome evals scored against historical golden diffs). See [evals.md](evals.md).

**Why:** Mechanical review and intent review answer "is this PR good?" Neither answers "is the agent that wrote it still behaving the way it used to?" Without an automated regression signal for the agents themselves, drift is invisible until a production incident. The Eval Gate catches scope creep, prompt-change degradation, and behavioral shifts before they ship. Every failed run auto-promotes to the eval set; every post-mortem must produce at least one new eval entry — that closes the loop and turns incidents into permanent improvements to the regression suite instead of forgettable retros.

## Merging the root issue merges everything

When all children of a root issue are in Ready, the root itself moves to Ready. Moving the root to Done is the signal to merge the whole feature branch — every child PR at once.

**Why:** It compresses the merge decision into one human action for one feature, rather than N actions for N children. The architect decides once: "this feature is ready to land." Everything underneath merges as a unit.

## Manual triggers over automated ones

Developers and architects move issues. Bots don't.

**Why:** A human moving an issue is a signal that they've committed to it — they've read the hierarchy, they understand the scope, they're picking it up. An automated trigger skips all of that and creates work that nobody has mentally committed to.

## Clarifying questions happen in the issue, not in Slack

When the Evaluation Agent has questions, it posts them as comments on the issue. The human responds there. Not in Slack, not in a video call, not in a separate document.

**Why:** Slack messages disappear into the scroll. Meeting decisions live in someone's memory. Issue comments are permanent, searchable, and visible to anyone who picks up the work later. When a new developer reads the issue six months from now, the full conversation about why it was built this way is right there.

## Human review is non-negotiable

Every PR gets a human review before the child issue moves to Ready. No exceptions. The Code Review Agent does a first pass, but it does not approve.

**Why:** AI-generated code can be subtly wrong in ways that pass tests but miss the point. Readability, elegance, and whether the change fits the product direction are things only a human can judge. The agent pass catches mechanical issues so the human has energy left for the hard parts.

## Code review is art, not science — keep the agent in the mechanical lane

The Code Review Agent checks for security gaps, missing tests, and pattern violations. It does not judge whether the code is readable, whether names are good, or whether the design makes sense.

**Why:** Readability and elegance are things experienced humans evaluate. An agent that tries to review "quality" will generate plausible-looking but shallow feedback — and worse, it will make humans trust it when they shouldn't. Keeping the agent's scope narrow and well-defined keeps the human reviewer's role clear and irreplaceable.

## No test-driven development for agent-driven work

Agents write the feature first, tests second. A feature child moves to Review when its code PR is up. Its companion test child is a separate issue with a separate agent and a separate PR.

**Why:** TDD's value is in shaping a human's thinking before they write code. Agents don't benefit from that loop the same way. Splitting feature and tests into separate child issues makes each PR focused and gives the testing agent clean scope. A feature isn't **Done** until its tests pass — but it is ready to move through the pipeline once its own code is reviewable.

## Human override on the Evaluation Agent

The Evaluation Agent decides when an issue is ready for implementation. A human architect can override that decision at any time — force ready, or send back to Backlog.

**Why:** The agent's definition of "good" evolves as the team uses it. Trust is earned, not assumed. An override path gives the team an escape valve while the agent is still learning the team's bar for "ready." This should stay in place even after trust is high — occasionally the agent will be wrong, and the humans need the ability to say so without editing the agent.

## Start with small changes

This workflow is scoped for small, well-defined changes — the kind where a root issue has three or four children. Not a major feature rewrite.

**Why:** There are a lot of moving pieces here. Evaluation, hierarchy building, per-child sequencing, per-child review, Ready coordination, root-level merge. Getting all of that right for a small change builds confidence. Once the team trusts the workflow for small changes, expanding to medium and large changes becomes a matter of adding steps, not redesigning the system.

## Handle in-progress work carefully

If a change affects an issue that's already in progress, don't modify that issue. Create a new one.

**Why:** Work that's in progress has momentum. An agent is already building against the current spec. Changing the spec mid-flight causes confusion and rework. A new issue that complements the in-progress work keeps everything clean — the original work finishes as planned, and the augmentation follows.

## Technology agnostic

We don't prescribe Linear, Jira, GitHub, or any specific tool. The workflow is described in terms of lanes, issues, comments, parent/child, and PRs.

**Why:** Every team has their stack. What matters is the pattern — safe zones around automated lanes, hierarchy expressing dependencies, architect-driven sequencing, human-gated review. If your tool supports these concepts (and they all do), the workflow applies. The specific vehicle for signaling a transition (webhook, label, status) will differ; the opinions do not.

## Agents don't talk to each other

There's no agent-to-agent communication channel. Agents communicate through the same artifacts humans use: issue comments, PR descriptions, code.

**Why:** If agents are passing context through a hidden channel, humans lose visibility. Everything that matters should be somewhere a human can read it. This also prevents the "telephone game" problem where context degrades as it passes through multiple agents — each one reads from the same canonical source (the issue, the PR, the code), not from each other.

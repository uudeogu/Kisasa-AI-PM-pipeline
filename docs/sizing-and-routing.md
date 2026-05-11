# Sizing and Routing

Every child issue in this workflow gets exactly one specialist agent (see [opinions.md](opinions.md) — "One agent per child issue"). What the v1 framework leaves implicit is that not every child issue is the same size, and not every agent run should use the same model.

A 2-line dependency bump and a 600-line cross-cutting refactor look identical to the orchestrator unless we size them. And a Haiku-class model running a 1-point doc tweak costs a fraction of the same task on Opus, with no quality difference. The cost-and-quality lever here is one of the largest in the framework.

## Three numbers per issue

Sizing in this workflow is **three numbers**, not one. Each captures a different thing that matters:

- **Story points** — Fibonacci 1 / 2 / 3 / 5 / 8. Captures complexity, risk, and uncertainty. Same scale humans use for human work.
- **ACUs (Agent Compute Units)** — 1 ACU is roughly 15 minutes of active agent work. Captures expected agent time.
- **Token budget** — Roughly 200 input tokens per line of expected output. Captures cost ceiling.

A typical 1-point child is 1 ACU and a small token budget. A typical 5-point child is 3-4 ACUs and a much larger budget. The three numbers move together but not identically — a 1-point change with high uncertainty (a security fix in an unfamiliar file) is still 1 point, but ACUs and budget should reflect the exploration cost.

### Who emits the numbers

The Evaluation Agent emits the three numbers when it decomposes a root issue into children. It writes them into the child issue's description, in a structured block the rest of the pipeline can read.

This is the same agent that already understands the codebase, the product, and the specialist roster. It's qualified to size — the same way it's qualified to decompose. Adding a dedicated Sizing Agent would add latency without obvious accuracy gain in v1.

The architect can override any of the three numbers in To-Do. Overrides are expected — sizing is the part of evaluation that calibrates fastest as the team uses the workflow.

## The hard split rule

Any child issue with more than 5 story points OR more than 4 ACUs is **automatically returned to Evaluation** for further breakdown. No specialist agent ever runs on an oversized child.

The reason is reliability. Agent runs that span 5+ ACUs accumulate drift — the agent's context gets noisier, intermediate decisions compound, and the final PR is harder to review. Cheaper-and-more-reliable beats bigger-and-flakier every time. If a child can't be done in 4 ACUs, it isn't one child.

The split is recursive. A 7-point child that gets returned might come back as a 4-point and a 3-point. If those still don't fit, they get split again. The orchestrator doesn't run anything on the original oversized issue until its descendants fit.

## Confidence-based approach

Confidence is independent of size. A 1-point change can be low confidence (we're not sure what the right fix is) and a 5-point change can be high confidence (we know exactly what to build). The agent emits confidence as a third axis alongside the size numbers.

Three confidence levels, three approaches:

- **Low** → **Spike issue.** Investigation only. No PR. The implementation agent's job is to read code, propose options as comments, and update the issue description with findings. The Evaluation Agent picks up the spike's output and re-decomposes with higher confidence.
- **Medium** → **Story with plan-first workflow.** The implementation agent must produce a written plan (in the child issue or PR description) before writing code. The architect can review the plan and redirect before tokens are spent on implementation.
- **High** → **Story with full PR allowed.** Standard flow — agent writes code and opens a PR without a separate plan step.

This is the same Spike-Story-PR ladder the CleanOps product-management workflow uses for inbound work, applied to dev pipeline output instead of product input. The pattern is: low confidence becomes investigation, medium becomes investigation-then-implementation, high becomes direct implementation.

## Model routing

```
            Router (inside Evaluation)
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   1 pt           2-3 pts           5+ pts
  mechanical      scoped           cross-cutting
       │               │               │
       ▼               ▼               ▼
   Haiku           Sonnet            Opus
  (single-shot)  (plan-first)    (plan + extended
                                  thinking +
                                  checkpoints)
```

The Router picks the model **by size**, not by specialty. The backend-specialist exists as `backend-specialist-haiku`, `backend-specialist-sonnet`, and `backend-specialist-opus` — same generated prompt, same context corpus, three runtime targets. Specialist and model are a 2D matrix, not a 1D list.

The cost difference is large and the quality difference on small tasks is not. Industry data (AWS, Anthropic, Inworld) puts well-tuned routing at 50-80% cost reduction with no measurable quality loss on the small end. This is the single largest cost lever in the framework.

### Routing rules

- **1 point + mechanical** (rename, dependency bump, doc tweak, type fix) → Haiku, single-shot, no separate plan step
- **2-3 points + scoped** (one component, one endpoint, one well-defined change) → Sonnet, Explore → Plan → Implement → Verify workflow
- **5 points + cross-cutting** (touches multiple modules, requires reasoning across systems) → Opus, plan-first with extended thinking and at least one human checkpoint between plan and implementation

Anything that's failed at a lower tier escalates up (see below). Anything that's succeeded at a higher tier doesn't downgrade — the Router doesn't try to be clever about reusing context across tiers in v1.

## Cost ceiling and runtime guardrails

Three guardrails wrap every agent run:

### Cost ceiling watchdog

If a running agent hits **2× its budgeted tokens** without producing a PR, the orchestrator pauses it. The agent posts a structured comment summarizing what it tried, what it learned, and where it got stuck. A human reads the comment and chooses one of three things:

- **Continue** — extend the budget, the agent was on a productive path
- **Split** — return the issue to Evaluation for further decomposition; the partial work informs the split
- **Kill** — abandon the run; the issue goes back to To-Do or Backlog

The watchdog exists because the failure mode for agents isn't "agent gives up" — it's "agent keeps trying" indefinitely. Letting an agent grind through 10× its budget on a stuck path is the most common way to blow real money on autonomous workflows.

### Time-box per ACU

15 minutes per allocated ACU is a hard cap. An agent allocated 3 ACUs has 45 minutes before it must produce something — a PR, a partial-progress comment, or a structured failure note. On timeout, the run is killed and the issue is flagged for human attention.

Time-boxing is independent of token-boxing. The two together catch different failure modes — token-box catches "agent is wasting tokens," time-box catches "agent is wall-clock stuck."

### Escalation ladder

When a run fails (returns to In Progress with a structured failure note from the Eval Gate, or aborts mid-run):

- **Fail 1×** → retry on the same tier
- **Fail 2×** → Router auto-upgrades to the next tier (Haiku → Sonnet → Opus)
- **Fail 4×** → page the architect; no further automated retries

The "fail 2× to upgrade" rule exists because the most common reason for repeated failure on a small task is that the task was misclassified as small. Upgrading the model after two failures is cheaper than a human re-evaluation, and the higher-tier model usually finishes what the lower-tier one couldn't.

The "fail 4× to page" rule exists because anything that's defeated two tiers of models has something structurally wrong with it — the issue is incoherent, the codebase has a problem the agent can't see, or the test infrastructure is broken. A human needs to look.

## Interaction with the rest of the workflow

Sizing happens **inside Evaluation**, before the issue moves to To-Do. By the time the architect looks at the To-Do hierarchy, every child has its three numbers and a routing decision attached. The architect can override any of it — or split a child further, or merge two children — before moving anything to In Progress.

The Eval Gate (see [evals.md](evals.md)) reads the size and the routing decision to decide which evaluation tiers to run. A 1-point Haiku run gets a Tier 1 schema validation and nothing else. A 5-point Opus run gets all three tiers plus similarity scoring. The gate's depth tracks the run's stakes.

The bug fix workflow (see [bugfix.md](bugfix.md)) has its own simplified sizing — bugs are almost always 1-2 points and high confidence by definition (the correct behavior is known). The full Router runs for bugs the same way, but the size distribution is narrower.

## What sizing doesn't do

- **Sizing doesn't replace human judgment.** The architect can override any number, any tier, any confidence level. Sizing is a default, not a decree.
- **Sizing doesn't predict business value.** RICE, prioritization, and roadmap decisions are upstream — sizing is about execution, not selection.
- **Sizing doesn't roll up.** A root issue's "size" is not the sum of its children. Children are sized; roots aren't. The framework operates on child issues.

## What it enables

Once sizing and routing are in place:

- **Cost becomes observable.** Per-issue spend, per-tier spend, model mix, and budget burn are all derivable from the three numbers and the runtime logs. The dashboard writes itself.
- **Triage gets honest.** "Too big for an agent" stops being a vibe and becomes a rule (>5pts or >4 ACUs). The architect can split confidently instead of hand-wringing.
- **Failure modes get diagnosable.** A child that fails Haiku, succeeds on Sonnet escalation, and ships clean isn't a mystery — it was misclassified, the escalation caught it, here's the trace. Patterns accumulate; the Evaluation Agent's sizing calibration improves.
- **The framework scales without a redesign.** New tiers (a future Sonnet-mini, an even-more-capable Opus successor) slot into the Router without touching anything else. New specialty agents pick up the same 2D matrix automatically.

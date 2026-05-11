# Intake

Work doesn't show up in your tracker as a well-written Jira ticket. It shows up as a customer call, a forwarded email, a Slack thread, an NPS comment, a support escalation, or a voicemail. The Intake lane is the safe zone that sits in front of Backlog and turns any of those into something the rest of the workflow can pick up.

```
[channels] ──▶ Intake ──▶ Backlog ──▶ Evaluation ──▶ ...
                 │
            no agents
            write code
            here
```

If you don't formalize Intake, one of two things happens. Either the PM transcribes everything by hand from memory and the framework starts from a thin issue. Or work bypasses the framework entirely — somebody pings the engineer, the engineer fixes it, no issue, no trace. Both fail in the same way: the workflow's first lane only sees a subset of what's actually moving through the team.

## What counts as a channel

There's no fixed list. Teams accept what they actually use:

- **Customer calls** — sales calls, support calls, advisory-board conversations, recorded via Otter / Fireflies / Granola
- **Email** — `support@`, `sales@`, forwarded threads from execs
- **Slack / Teams** — channel threads, DMs that turn into requests
- **In-app feedback / NPS** — comments submitted from the product itself
- **Support ticket escalations** — Zendesk / Intercom tickets that cross a severity threshold
- **Voicemail / phone** — yes, this is still a real channel for some teams

The principle is the same as the workflow itself: more channels are fine as long as each one routes through Intake. The way bugs sometimes bypass the full workflow to use [bugfix.md](bugfix.md) is the same shape — a lighter path that still goes through a defined lane, not no path at all.

## The Intake Agent

**When:** A new piece of inbound content lands on a channel
**Job:** Normalize it, search for matches in the tracker, decide whether to append to an existing issue, create a new one, or park for human review
**Communicates via:** Issue comments and new issue descriptions — same as every other agent

The Intake Agent is generated from the same business and product context as the rest of the agents (see [agent-generation.md](agent-generation.md)). It needs the customer language, the product vocabulary, and the team's understanding of what's actually a feature request vs. what's noise. A generic intake agent will create three duplicate issues for "the export is slow" because it doesn't know the team already calls that "the orders-export latency problem."

### What the agent does

1. **Receives the raw content** — transcript, email body, Slack thread, NPS comment
2. **Normalizes to a canonical schema** — channel, source identity (who said it), timestamp, content, any extracted intent
3. **Redacts PII and secrets** — names, emails, account numbers, API keys, anything sensitive — *before* the content enters any prompt or trace log
4. **Searches the tracker** — looks for open issues that match the intent, including recently closed ones if regression is plausible
5. **Decides** — append, create, or park (see below)
6. **Writes traceability** — every action the agent takes leaves a comment or a description line that says where it came from

### Search-first, not create-first

The default action is to append, not create. If the agent finds a high-confidence match against an existing issue, it adds a "Call Notes" comment to that issue with the new evidence — the quote, the source, the date. The issue accumulates customer voice over time instead of fragmenting into duplicates.

New issues are created only when the agent's match confidence is below the threshold AND its create-confidence is above it. Everything in between gets parked in Triage for a human.

The confidence thresholds are channel-specific. A voicemail is noisier than a Confluence comment. An NPS one-liner is lower-signal than a 30-minute customer call. Tuning these is part of the team's setup, not something the framework hardcodes.

## Traceability

Every issue or comment the Intake Agent produces must include a source header in the description:

```
Sourced from: <channel> — <speaker or sender> (<YYYY-MM-DD>)
```

This rule exists because six months from now, someone will read the issue and need to know whether this came from one customer's frustration on a call or from a recurring NPS theme. Without the header, the context evaporates. With the header, the workflow stays auditable end-to-end — from a customer's actual words, through Backlog, Evaluation, implementation, all the way to a merged PR.

## PII and secrets redaction

PII and secrets are removed **before** content enters any prompt, any trace log, any database row that an agent can read later. Not after. Not "we'll filter it at display time." Before.

The reason is blast radius. Once a customer's email address has been pasted into an LLM prompt, it has potentially been retained by the model provider, cached, logged, or used in a future trace. Treating intake as the redaction boundary means the rest of the workflow never holds raw PII, and a leak at the agent layer is impossible to produce.

This isn't optional for any team handling customer data. It's the one rule in this doc that's load-bearing for compliance, not just hygiene.

## The decision: append, create, or park

```
                    Match against open
                    or recently closed
                        issues
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        high match   low match    low match
        confidence   high create  low create
              │     confidence  confidence
              ▼           ▼           ▼
         Append to    Create new    Park in
        existing      issue with    Triage
        issue         "Sourced      (human
                      from:" head   review)
```

The three outcomes are independent — you can have a high match-confidence and *also* a high create-confidence (e.g., a customer raised a related-but-distinct issue on the same call). In that case the agent does both: append to the existing issue, and create a new one, with cross-links.

## Human override

The same override rule that runs through the rest of the workflow applies here. A PM can create an issue directly without going through Intake. The Intake Agent is there to handle the volume of inbound material the team can't process by hand — it's not a gate.

What you should *not* do is bypass Intake when the source is one of the supported channels. If a customer call comes in, run it through Intake even if you already know what the issue is. The reason is the same as why we don't skip Evaluation for "obvious" features — the agent's value compounds when its corpus includes every real signal, not just the ones nobody bothered to skip.

## What Intake doesn't do

- **Intake doesn't prioritize.** It doesn't decide what's important. Priority is a downstream decision by the PM and architect in Backlog.
- **Intake doesn't escalate to engineers directly.** Even a Sev 1 support ticket goes through Intake → Backlog. Critical bugs use [bugfix.md](bugfix.md) once they're in the tracker, not before.
- **Intake doesn't speak to the customer.** No replies are sent from this lane. Customer communication stays with the people who own those channels (sales, support, success).
- **Intake doesn't move issues to Evaluation.** That's a human decision in Backlog — same as every lane-to-lane transition in this workflow.

## What it enables

Once intake is formalized, three things become possible that aren't otherwise:

- **Customer voice survives.** The exact quote that triggered an issue is in the issue description, not lost in someone's Slack scroll.
- **Duplicate suppression scales.** A team that gets 50 NPS comments a week can't manually dedupe them; the agent can, and append-by-default means recurring themes accumulate evidence on the same issue rather than fragmenting.
- **Trace lineage is complete.** A merged PR can be walked backward through the feature branch → root issue → call transcript → customer who originally said it. That's the audit trail every regulated team eventually needs and every other team eventually wants.

## A worked example

A customer call happens. The transcript lands in the inbox:

> *"...and honestly the worst part is exporting orders. I have 800 orders this month and the CSV download took like four minutes. We need it faster, or maybe just a way to schedule it overnight."*

1. **Intake Agent normalizes** the transcript into the canonical schema — channel: `customer-call`, source: `BigCorp account, sales call 2026-05-11`, content: the quote above.
2. **PII redaction** strips the customer's name and the account identifier from the prompt context. The source header retains "BigCorp account" as a coarse label.
3. **Search** finds an existing open issue: `orders-export performance`. Match confidence is high.
4. **Decision: append.** Agent adds a comment to the existing issue:
   > **Call Notes** — Sourced from: customer-call — BigCorp account (2026-05-11)
   >
   > Customer reported 4-minute CSV download on 800 orders. Suggested workaround: scheduled overnight export.
5. **Also detected** — the "scheduled overnight export" phrase is below the create-confidence threshold but above the discard threshold. Agent parks a candidate "Scheduled exports" issue in Triage with a link to the call.
6. **PM picks up** the parked candidate the next morning, decides it's worth pursuing, moves it to Backlog as a new root issue. The original performance issue now has new evidence; the scheduled-export idea has a fresh home.

No agent fired any code. No PR was opened. But the next time the architect grooms the Backlog, both issues are richer than they would have been if the call hadn't been formalized through intake.

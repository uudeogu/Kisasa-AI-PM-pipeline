# Workflow

The full development workflow, column by column. Technology agnostic — this applies whether you use Linear, Jira, or sticky notes on a wall. What matters is the rules at each stage.

## Backlog

**Owner:** Humans (PM, stakeholders)
**Agents:** None

The backlog is a safe space. No agents trigger here. This is where PMs, stakeholders, and the team work through ideas, customer feedback, and priorities at their own pace.

Issues land here from:
- Customer conversations and meeting transcripts
- Feedback portals and support channels
- Internal ideas and technical debt

The PM shapes these into well-formed issues with enough context for the next stage. There is no rush. Nothing automated is watching this column.

## To-Do

**Owner:** PM + Evaluation Agent
**Trigger:** PM moves issue from Backlog to To-Do

When an issue moves to To-Do, an evaluation agent picks it up. This agent understands the codebase and the product. Its job is to read the issue and identify anything unclear or missing.

### What the agent does

1. Reads the issue in full
2. Cross-references against the codebase and product context
3. Posts clarifying questions as comments on the issue

Examples of clarifying questions:
- "This references the address form — is this the checkout address or the shipping address component?"
- "The acceptance criteria mention a new API endpoint. Should this extend the existing `/users` resource or be a separate endpoint?"
- "Which library handles date formatting in this project? I see both `dayjs` and `date-fns` in the dependencies."

### The back-and-forth

The agent tags the relevant person (PM, developer, designer) in each question. They respond in the issue comments. The agent reads the response, may ask follow-up questions, and this continues until the agent has no more questions.

**All context stays in the ticket.** Not in Slack, not in a separate doc — in the issue comments where anyone picking up the work can see the full conversation.

### When is it ready?

The agent signals that it has no more questions (e.g., a comment saying "No further questions — this issue is ready for implementation"). At this point, the issue sits in To-Do waiting for a developer to pick it up.

**The PM does not move it forward.** The developer does, when they're ready.

## In Progress

**Owner:** Developer + Implementation Agents
**Trigger:** Developer manually moves issue from To-Do to In Progress

This is a **manual trigger** and that's intentional. The developer is signaling: "I'm picking this up now." This mirrors how real teams work — developers pull work when they have capacity, not when a system pushes it to them.

### Sequencing work

For a feature that touches multiple layers (backend, frontend, tests), **do not fire everything off at once**. Sequence it:

1. **Backend first** — API changes, data model updates, business logic
2. **Backend tests** — Integration tests for the new/changed endpoints
3. **Frontend** — UI changes that consume the now-stable backend contract
4. **E2E tests** — Playwright tests that validate the full flow

Why? If something changes in the backend during implementation (a payload field gets renamed, an endpoint gets restructured), you haven't wasted work on frontend code that assumed the old contract. This is how good teams already work — we're encoding that practice, not bypassing it.

### Agent implementation

Each piece of work can be assigned to a different agent with a different specialty:
- A backend agent that knows the API patterns and data models
- A frontend agent that knows the component library and design system
- A testing agent that knows the test framework and validation patterns

The developer controls the sequencing. They move the backend issue to In Progress first, wait for the PR, review it, and then move the frontend issue over. The agents work fast, but the human controls the pace.

### What gets produced

- A branch with the implementation
- A pull request with a clear description
- Automated tests passing in CI

## Review

**Owner:** Human developer
**Trigger:** PR is created and CI passes

A human reviews the PR. This is non-negotiable. The developer:
- Reads the code changes
- Checks that the implementation matches the issue requirements
- Verifies the tests are meaningful (not just passing but actually testing the right things)
- Reviews the Playwright E2E test recordings if applicable
- Merges when satisfied

## Done

The issue is complete. The code is merged, tests pass, and the feature is verified.

Deployment to production is a separate decision, controlled by the team's release process — not by this workflow.

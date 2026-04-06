# Opinions

Every decision in this workflow is opinionated. Here's what we chose and why.

## "Just because we can automate doesn't mean we should"

AI agents can do a lot. They can create issues from customer feedback, write code, run tests, merge PRs, and deploy — all without a human touching anything. We deliberately chose not to do that.

**Why:** Fully autonomous pipelines optimize for speed at the cost of judgment. When something goes wrong (and it will), you need a human who understood the context at each step. More importantly, the intermediate human decisions — which issue to pick up next, whether to do backend or frontend first, whether this PR actually makes sense — are where the real quality comes from.

## Manual triggers over automated ones

The developer moves issues to In Progress, not a bot. The developer decides when to start frontend work, not a scheduler.

**Why:** Developers pulling work when they're ready is a feature, not a limitation. It means they've read the issue, they understand the context, and they're committing to it. An automated trigger skips all of that and creates work that nobody has mentally committed to.

## Clarifying questions happen in the issue, not in Slack

When the evaluation agent has questions, it posts them as comments on the issue. The human responds there. Not in Slack, not in a video call, not in a separate document.

**Why:** Slack messages disappear into the scroll. Meeting decisions live in someone's memory. Issue comments are permanent, searchable, and visible to anyone who picks up the work later. When a new developer reads the issue six months from now, the full conversation about why it was built this way is right there.

## Sequence work, don't parallelize everything

Backend before frontend. Integration tests before E2E. Even though agents can work in parallel, we choose to sequence.

**Why:** If you build frontend and backend in parallel and the backend contract changes mid-implementation, the frontend work is wasted. Sequencing is how experienced teams already work — the backend developer finishes the API, the frontend developer builds against the real contract. We're not going to throw away that practice just because AI agents are fast.

## Start with small changes

We scoped this workflow for small, well-defined changes — the kind where you'd update one or two issues. Not a major feature rewrite.

**Why:** There are a lot of moving pieces here. Evaluation agents, implementation agents, issue comments, PR reviews, test validation. Getting all of that right for a small change builds confidence. Once the team trusts the workflow for small changes, expanding to medium and large changes becomes a matter of adding steps, not redesigning the system.

## Handle in-progress work carefully

If a change affects an issue that's already in progress, don't modify that issue. Create a new one.

**Why:** Work that's in progress has momentum. A developer (human or agent) is already building against the current spec. Changing the spec mid-flight causes confusion and rework. A new issue that complements the in-progress work keeps everything clean — the original work finishes as planned, and the augmentation follows.

## Technology agnostic

We don't prescribe Linear, Jira, GitHub, or any specific tool. The workflow is described in terms of columns, issues, comments, and PRs.

**Why:** Every team has their stack. What matters is the pattern — Backlog is a safe space, To-Do triggers evaluation, In Progress triggers implementation, Review is human, Done is done. If your tool supports these concepts (and they all do), the workflow applies.

## Human reviews are non-negotiable

Every PR gets a human review before merge. No exceptions.

**Why:** AI-generated code can be subtly wrong in ways that pass tests but miss the point. A human reviewer catches "this technically works but it's not what we wanted" problems. It also keeps the team aware of what's changing in the codebase — nobody should be surprised by what's in production.

## Agents don't talk to each other

There's no agent-to-agent communication channel. Agents communicate through the same artifacts humans use: issue comments, PR descriptions, code.

**Why:** If agents are passing context through a hidden channel, the humans lose visibility. Everything that matters should be in a place where a human can read it. This also prevents the "telephone game" problem where context degrades as it passes through multiple agents.

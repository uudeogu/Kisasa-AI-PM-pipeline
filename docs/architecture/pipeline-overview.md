# Kisasa AI PM Pipeline — Architecture Overview

## Pipeline Stages

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Intake  │──▶│ Research  │──▶│ Roadmap  │──▶│  Build   │──▶│    QA    │──▶│  Launch  │──▶│  Retro   │
│Discovery │   │Feasibility│   │ Planning │   │  & Ship  │   │Validation│   │ Handoff  │   │ Learning │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

## Stage Details

### Stage 1: Intake & Discovery
- **Input:** Client conversations, emails, Slack threads, meeting transcripts
- **AI Role:** Extract requirements, generate structured project briefs
- **Output:** Project brief with scope, goals, constraints, and division routing (Ventures/Labs/Strategy)

### Stage 2: Research & Feasibility
- **Input:** Project brief
- **AI Role:** Market scan, competitor analysis, technical feasibility assessment, risk scoring
- **Output:** Feasibility report with recommendations and risk matrix

### Stage 3: Roadmap & Planning
- **Input:** Approved feasibility report
- **AI Role:** Generate phased roadmap, break epics into stories, estimate effort from historical data
- **Output:** Roadmap with milestones, stories with acceptance criteria, RICE-scored backlog

### Stage 4: Build & Ship
- **Input:** Sprint backlog
- **AI Role:** Code generation assist, PR reviews, test writing, scope creep detection
- **Output:** Shipped increments, CI/CD artifacts

### Stage 5: QA & Validation
- **Input:** Shipped increments + acceptance criteria
- **AI Role:** Generate test cases, run regression checks, triage client UAT feedback
- **Output:** Validation report, bug tickets

### Stage 6: Launch & Handoff
- **Input:** Validated product
- **AI Role:** Auto-generate docs, runbooks, onboarding guides
- **Output:** Production deployment, client handoff package

### Stage 7: Retrospective & Learning
- **Input:** Project outcomes, estimates vs actuals
- **AI Role:** Analyze performance, extract learnings, feed back into pipeline
- **Output:** Updated estimation models, process improvements

## Division Routing

| Division | Trigger | Pipeline Focus |
|----------|---------|----------------|
| Ventures | New product idea, investment opportunity | Full pipeline, heavy on Stages 1-4 |
| Labs | System modernization, architecture work | Stages 2-4, emphasis on technical feasibility |
| Strategy | Developer ecosystem, adoption planning | Stages 1-3, emphasis on research and roadmap |

## Tech Stack

- **Language:** Python (backend agents) + TypeScript (dashboard)
- **AI Layer:** Claude API via Anthropic SDK
- **Orchestration:** Claude Agent SDK or LangGraph
- **Data:** PostgreSQL + vector DB (for RAG over project history)
- **Intake Connectors:** Slack API, Gmail API, Zoom API (meeting transcripts)
- **PM Integration:** Linear API + Notion API
- **Frontend:** Next.js + Vercel AI SDK
- **CI/CD:** GitHub Actions
- **Observability:** OpenTelemetry

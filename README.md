# Kisasa AI PM Pipeline

AI-powered product development pipeline for [kisasa.io](https://kisasa.io) — automating the journey from client intake to shipped product.

## Pipeline Stages

1. **Intake & Discovery** — Extract requirements from client conversations, generate project briefs
2. **Research & Feasibility** — Market scanning, competitor analysis, technical feasibility
3. **Roadmap & Planning** — AI-generated roadmaps, stories, and effort estimates
4. **Build & Ship** — Code assist, PR reviews, scope creep detection
5. **QA & Validation** — Auto-generated test cases, regression checks, UAT triage
6. **Launch & Handoff** — Documentation, runbooks, onboarding guides
7. **Retrospective & Learning** — Outcome analysis, feedback loop into pipeline

## Project Structure

```
├── src/
│   ├── agents/          # AI agent definitions
│   ├── pipeline/        # Pipeline stage implementations
│   │   ├── intake/      # Stage 1: Intake & Discovery
│   │   ├── research/    # Stage 2: Research & Feasibility
│   │   ├── roadmap/     # Stage 3: Roadmap & Planning
│   │   ├── build/       # Stage 4: Build & Ship
│   │   ├── qa/          # Stage 5: QA & Validation
│   │   ├── launch/      # Stage 6: Launch & Handoff
│   │   └── retro/       # Stage 7: Retrospective & Learning
│   ├── integrations/    # Third-party API connectors (Linear, GitHub, Slack)
│   └── utils/           # Shared utilities
├── docs/
│   ├── architecture/    # Pipeline architecture docs
│   └── research/        # Research sources and references
├── tests/
└── dashboard/           # Next.js frontend (future)
```

## Tech Stack

- **AI:** Claude API (Anthropic SDK)
- **Backend:** Python
- **Orchestration:** Claude Agent SDK
- **Data:** PostgreSQL + Vector DB
- **Frontend:** Next.js + Vercel AI SDK
- **CI/CD:** GitHub Actions

## Getting Started

```bash
# Clone the repo
git clone https://github.com/uudeogu/Kisasa-AI-PM-pipeline.git
cd Kisasa-AI-PM-pipeline

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Install dependencies
pip install -r requirements.txt

# Run the intake agent
python -m src.pipeline.intake.agent
```

## Divisions

The pipeline routes work across Kisasa's three divisions:

| Division | Focus |
|----------|-------|
| **Ventures** | Investment & new product development |
| **Labs** | System modernization & architecture |
| **Strategy** | Developer ecosystems & adoption planning |

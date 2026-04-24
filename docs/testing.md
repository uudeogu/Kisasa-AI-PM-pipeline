# Testing Strategy

How testing fits into the workflow. Three layers, each with a clear purpose and each owned by its own child issue.

## Unit & Integration Tests

**When:** Written by the test agent after the feature code is in Review
**Run:** In CI (GitHub Actions or equivalent)
**Environment:** Clean container — no cached dependencies, no local state

Unit and integration tests live in a separate child issue from the feature code. A backend feature child opens its PR, moves to Review, and passes review. At that point the architect moves the companion backend-tests child to In Progress, and the test agent writes tests against the already-reviewed feature code.

This is a deliberate split (see [opinions.md](opinions.md) — "No test-driven development for agent-driven work"). The feature child's PR is ready when its own code is reviewable; the feature itself is **Done** only when its tests also pass.

Integration tests hit real services, not mocks. If you mock the database and the mock diverges from the real thing, your tests pass but production breaks. Spin up the dependencies in containers (Docker Compose) and test against them.

### Environment matters

Tests must run in a clean, reproducible environment. Not on a developer's laptop with cached packages. A CI runner (or a dedicated test container) starts from scratch every time — install dependencies explicitly, use the same base image as production.

This catches the class of bugs where tests pass locally because of stale cached dependencies but fail in a clean environment (or vice versa).

## E2E Tests with Playwright

**When:** Written by the E2E test agent after the frontend child issue has reached Ready
**Run:** In CI as a separate action
**What it does:** Simulates real user interactions — clicking buttons, filling forms, navigating pages

The E2E child issue is a child of the frontend child in the hierarchy. It can't start until the frontend is complete, and the backend it depends on is already in Ready by that point too. The E2E agent has a stable feature branch to test against.

Playwright is our recommended framework for end-to-end testing. It:
- Runs in headless mode in CI (just get the report)
- Can run interactively for debugging (brings up a browser)
- Takes screenshots at each step so you can replay the test visually
- Simulates real user flows: login, form submission, navigation, error states

### What E2E tests cover

- Happy paths: user logs in, performs the action, sees the expected result
- Error paths: wrong password, invalid input, network failures
- Regression: the full product still works after this change, not just the new feature

### E2E tests are not optional

The evaluation agent should include E2E acceptance criteria in the issue. The testing agent writes Playwright tests against those criteria. This replaces most manual QA — the agent simulates what a human tester would click through.

A human may still manually validate the specific change in a release, but the assurance that nothing else regressed is built into the automated tests.

## The testing sequence

Expressed in the child-issue hierarchy:

```
Root feature
└── Backend
    ├── Backend tests (unit + integration)
    └── Frontend
        └── E2E tests (Playwright)
```

The architect moves children through In Progress in that order — backend first, its tests once the backend PR is in Review, frontend after backend tests are in Ready, E2E last. Every child hits Ready before siblings that depend on it kick off. E2E runs against a stable feature branch with real backend and real frontend.

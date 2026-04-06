# Testing Strategy

How testing fits into the workflow. Three layers, each with a clear purpose.

## Unit & Integration Tests

**When:** Written by the implementation agent alongside the code
**Run:** In CI (GitHub Actions or equivalent)
**Environment:** Clean container — no cached dependencies, no local state

Integration tests hit real services, not mocks. If you mock the database and the mock diverges from the real thing, your tests pass but production breaks. Spin up the dependencies in containers (Docker Compose) and test against them.

### Environment matters

Tests must run in a clean, reproducible environment. Not on a developer's laptop with cached packages. A CI runner (or a dedicated test container) starts from scratch every time — install dependencies explicitly, use the same base image as production.

This catches the class of bugs where tests pass locally because of stale cached dependencies but fail in a clean environment (or vice versa).

## E2E Tests with Playwright

**When:** Written by the testing agent after frontend implementation
**Run:** In CI as a separate action
**What it does:** Simulates real user interactions — clicking buttons, filling forms, navigating pages

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

1. Backend implementation + integration tests
2. Frontend implementation
3. E2E tests (Playwright)

E2E tests come last because they depend on both backend and frontend being stable. Running them earlier would just produce false failures.

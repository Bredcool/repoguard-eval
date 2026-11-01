# Frontend Testing

## 1. Overview

The RepoGuard-Eval frontend uses Vitest and React Testing Library for automated testing.

The test environment is configured with jsdom.

Current testing goals:

- Verify reusable component behavior.
- Verify feedback-state rendering.
- Verify Redux state management.
- Verify application providers.
- Verify route configuration.
- Verify navigation and layout integration.

## 2. Testing Stack

| Tool | Responsibility |
| --- | --- |
| Vitest | Test runner and assertions |
| jsdom | Browser-like DOM environment |
| React Testing Library | React component testing |
| Testing Library Jest DOM | DOM assertions |
| Testing Library User Event | User interaction simulation |
| Playwright | Browser automation dependency; no completed E2E suite is documented in this phase |

## 3. Test Structure

Tests are located under:

apps/web/tests/
├── setup.ts
├── app/
│   ├── providers/
│   ├── router/
│   └── store/
└── components/
    ├── feedback/
    ├── layout/
    └── ui/

Tests are organized according to the application areas they verify.

## 4. Test Environment

Vitest configuration is located in apps/web/vite.config.ts.

The current configuration uses:

- jsdom as the test environment.
- tests/setup.ts as the setup file.
- Automatic mock clearing.
- Automatic mock restoration.
The setup file imports the Vitest integration for Jest DOM and performs React Testing Library cleanup after each test.

## 5. Running Tests

Run all frontend tests from the repository root:
npm test

Run tests in watch mode:
npm run test:watch --workspace @repoguard/web

Run TypeScript validation:
npm run typecheck

## 6. Current Test Coverage Areas

UI Components
Tests cover:

- Button rendering and behavior.
- Card rendering.
- Badge rendering.
Feedback Components
Tests cover:
- Loading state.
- Empty state.
- Error state.
- Success state.
Redux Store
Tests cover:
- Initial state.
- Sidebar state transitions.
- State updates through actions.
- Store dispatch and state access.
Application Providers
Tests verify that:
- Redux context is available.
- TanStack Query context is available.
- Provider children render correctly.
Routing
Tests cover:
- Route metadata.
- Registered page rendering.
- Not-found behavior.
- Navigation between pages.
- Active navigation state.
Layout Integration
Tests cover:
- Application layout rendering.
- Header behavior.
- Sidebar navigation.
- Sidebar expanded and collapsed states.

## 7. Verified Phase 1 Results

The following results were confirmed during Phase 1 verification:
Verification Result
TypeScript typecheck Passed
Vitest test files 15 passed
Automated tests 115 passed
Failed tests 0
Vite production build Passed
Transformed modules 126
npm audit vulnerabilities 0

Latest confirmed test summary:
Test Files  15 passed (15)
Tests       115 passed (115)

Latest confirmed production build:
vite v7.3.7 building client environment for production...
✓ 126 modules transformed.
✓ built in 1.51s

The results represent the Phase 1 verification run. Re-run the commands after subsequent code changes.

## 8. Testing Guidelines

When adding new functionality:

1. Add tests alongside the relevant application area.
2. Test observable behavior rather than implementation details.
3. Test important user interactions.
4. Test loading, empty, error, and success states where applicable.
5. Keep tests independent.
6. Run the complete test suite before considering a change complete.

## 9. Current Limitations

```text
- No completed Playwright E2E test suite is documented.
- No backend integration tests exist in this frontend phase.
- No API-driven evaluation workflow is available to test.
- No performance benchmark or load test has been established.
These areas can be introduced in later development phases.

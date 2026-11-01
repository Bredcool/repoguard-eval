# Frontend Architecture

## 1. Overview

The RepoGuard-Eval frontend is a React application built with TypeScript and Vite.

It uses a modular source structure to separate:

- Application initialization.
- Providers and application configuration.
- Routing.
- Global UI state.
- Reusable components.
- Feature-specific pages.
- Shared styles.

The current frontend is a foundation. Feature pages are placeholders and are not yet connected to a backend.

## 2. Technology Stack

| Technology | Responsibility |
| --- | --- |
| React | Component-based user interface |
| TypeScript | Static typing |
| Vite | Development server and production bundler |
| React Router | Client-side routing |
| Redux Toolkit | Global client-side UI state |
| React Redux | React integration for Redux |
| TanStack Query | Server-state management foundation |
| Vitest | Test runner |
| React Testing Library | Component and integration testing |
| Playwright | Browser automation dependency; E2E coverage is not yet established |

## 3. Source Structure

apps/web/src/
├── App.tsx
├── main.tsx
├── app/
│   ├── providers/
│   │   ├── AppProviders.tsx
│   │   └── queryClient.ts
│   ├── router/
│   │   ├── routeConfig.ts
│   │   ├── routeDefinitions.tsx
│   │   └── router.tsx
│   └── store/
│       ├── hooks.ts
│       ├── store.ts
│       └── uiSlice.ts
├── components/
│   ├── feedback/
│   ├── layout/
│   └── ui/
├── features/
│   ├── about/
│   ├── benchmarks/
│   ├── documentation/
│   ├── evaluations/
│   ├── overview/
│   ├── repositories/
│   └── results/
└── styles/
    ├── global.css
    ├── reset.css
    ├── tokens.css
    └── utilities.css

## 4. Application Entry Point

main.tsx
The frontend entry point initializes the React application.

It imports the global styles, enables React Strict Mode, applies application providers, and renders the root application component.
App.tsx
The root application component renders the configured React Router provider.

This keeps application initialization separate from route definitions.

## 5. Application Providers

AppProviders.tsx
The provider component currently wraps the application with:

- Redux Provider.
- TanStack Query QueryClientProvider.
This centralizes shared application context.
queryClient.ts
The shared QueryClient defines default query and mutation behavior.

Current defaults:
Option Value
Query stale time 60 seconds
Query garbage collection time 5 minutes
Query retry 1
Refetch on window focus Disabled
Mutation retry 0

These defaults can be adjusted as real API integration is introduced.

## 6. Feature Organization

Each feature has its own directory under features/.

Current feature areas:
Feature Responsibility
Overview Platform overview
Repositories Repository management interface
Benchmarks Benchmark discovery interface
Evaluations Evaluation workflow interface
Results Evaluation result interface
Documentation Documentation page
About Project information

Feature pages are currently placeholders. Backend integration and complete feature workflows are outside Phase 1.

## 7. Shared Components

Shared components are grouped by responsibility.
components/layout/
Contains the application shell:

- AppLayout.tsx
- Header.tsx
- Sidebar.tsx
- layout.css
components/ui/
Contains reusable interface primitives:
- Button.tsx
- Card.tsx
- Badge.tsx
components/feedback/
Contains reusable feedback components:
- LoadingState.tsx
- EmptyState.tsx
- ErrorState.tsx
- SuccessState.tsx

## 8. Styling Organization

Shared styles are located in styles/:

- reset.css: browser style normalization.
- tokens.css: shared design tokens.
- global.css: global application styles.
- utilities.css: reusable utility styles.
Component-specific styles are colocated with their respective component groups.

## 9. Architectural Boundaries

The frontend should follow these boundaries:

1. Application configuration belongs in app/.
2. Shared interface components belong in components/.
3. Feature-specific pages and logic belong in features/.
4. Shared global styles belong in styles/.
5. Backend communication should be introduced through explicit API and data-access modules when backend integration begins.
Avoid placing feature-specific business logic in generic UI components.

## 10. Adding a New Feature

A new frontend feature should generally:

1. Have its own directory under features/.
2. Contain its page components.
3. Define feature-specific logic close to the feature.
4. Reuse shared components where appropriate.
5. Register its route in the routing configuration.
6. Add navigation metadata if it should appear in the sidebar.
7. Include tests for its behavior.

## 11. Current Limitations

```text
- Feature pages are placeholders.
- No production API integration is implemented.
- No authentication flow is implemented.
- No persistent user data workflow is implemented.
- No backend-driven evaluation workflow is implemented.
These limitations are intentional for the Phase 1 frontend foundation.

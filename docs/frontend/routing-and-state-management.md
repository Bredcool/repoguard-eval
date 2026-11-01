# Routing and State Management

## 1. Overview

The frontend uses three complementary tools:

- React Router for navigation.
- Redux Toolkit for global client-side UI state.
- TanStack Query for server-state management.

Each tool has a separate responsibility.

## 2. Routing

Routing configuration is located in:

apps/web/src/app/router/
├── routeConfig.ts
├── routeDefinitions.tsx
└── router.tsx

routeConfig.ts
This file contains route metadata.

The AppRoute interface defines:

- path: route URL.
- label: navigation label.
- description: route description.
- group: navigation group.
- showInNavigation: whether the route appears in navigation.
The appRoutes object is the shared route metadata source used by navigation components.
routeDefinitions.tsx
This file defines the React Router route objects.

The application routes are nested under AppLayout, allowing the sidebar and header to remain visible while the page content changes through the layout's Outlet.

The not-found route is defined separately.
router.tsx
This file creates the browser router using createBrowserRouter and the shared route definitions.

## 3. Available Routes

Page Path Navigation Group
Overview / Workspace
Repositories /repositories Workspace
Benchmarks /benchmarks Workspace
Evaluations /evaluations Workspace
Results /results Workspace
Documentation /documentation Resources
About /about Resources

Unknown paths render the not-found page.

## 4. Adding a Route

To add a new page:

1. Create the page under the appropriate features/ directory.
2. Add route metadata to appRoutes in routeConfig.ts.
3. Add the corresponding route object to appRouteDefinitions in routeDefinitions.tsx.
4. Set showInNavigation to true if the route should appear in the sidebar.
5. Add or update tests for route configuration and navigation.
Keep route metadata and route rendering definitions synchronized.

## 5. Redux Toolkit

Redux Toolkit manages global client-side UI state.

Current store structure:
apps/web/src/app/store/
├── hooks.ts
├── store.ts
└── uiSlice.ts

store.ts
Configures the Redux store and registers the UI reducer.

The store exports:

- store
- RootState
- AppDispatch
uiSlice.ts
The current UI slice manages sidebar state.

State:
interface UIState {
    sidebarCollapsed: boolean
}

Available actions:

- toggleSidebar()
- setSidebarCollapsed(boolean)
hooks.ts
Provides typed React Redux hooks:
- useAppDispatch
- useAppSelector
Use these hooks in React components instead of repeatedly defining untyped dispatch and selector usage.

## 6. TanStack Query

TanStack Query is configured through the shared QueryClient in queryClient.ts.

It is intended for server-state concerns such as:

- Fetching repository data.
- Fetching benchmark definitions.
- Monitoring evaluation jobs.
- Retrieving evaluation results.
- Managing asynchronous API requests.
No real API queries or mutations are implemented in the current Phase 1 foundation.

## 7. Choosing the Correct State Tool

State Type Recommended Tool
Sidebar collapsed/expanded Redux Toolkit
Global UI preferences Redux Toolkit
Data fetched from an API TanStack Query
API loading and error state TanStack Query
Local component-only interaction React component state

Avoid storing server responses in Redux when TanStack Query is responsible for managing that server data.

## 8. Provider Hierarchy

The current provider hierarchy is:
React StrictMode
└── AppProviders
    ├── Redux Provider
    │   └── QueryClientProvider
    │       └── App
    │           └── RouterProvider

This makes the Redux store and QueryClient available throughout the application.

## 9. Testing Considerations

```text
Routing and state-management tests should cover:
- Route metadata correctness.
- Page rendering for registered routes.
- Not-found behavior.
- Navigation between pages.
- Sidebar state transitions.
- Redux state initialization and updates.
- Provider availability.
See testing.md for the current testing strategy.

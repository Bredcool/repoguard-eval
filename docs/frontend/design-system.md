
# Frontend Design System

## 1. Overview

The RepoGuard-Eval frontend uses a shared styling foundation and reusable React components.

The design system is intended to keep visual behavior consistent and make future interface development easier.

## 2. Styling Structure

Global styles are located in:

apps/web/src/styles/
├── reset.css
├── tokens.css
├── global.css
└── utilities.css

File Responsibility
reset.css Normalize browser defaults
tokens.css Define shared design tokens
global.css Apply global application styling
utilities.css Provide reusable utility classes

Component-specific styles are colocated with their component groups.

## 3. Component Style Organization

apps/web/src/components/
├── layout/
│   ├── AppLayout.tsx
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── layout.css
├── ui/
│   ├── Badge.tsx
│   ├── Button.tsx
│   ├── Card.tsx
│   └── ui.css
└── feedback/
    ├── EmptyState.tsx
    ├── ErrorState.tsx
    ├── LoadingState.tsx
    ├── SuccessState.tsx
    └── feedback.css

## 4. Application Layout

The application shell consists of:

- Sidebar navigation.
- Header.
- Main content area.
AppLayout.tsx composes these components and renders the active route through React Router's Outlet.

The sidebar supports expanded and collapsed states.

The layout stylesheet also includes responsive rules for narrower viewports.

## 5. Reusable UI Components

Button
A reusable interactive control for user actions.
Card
A reusable container for grouping related interface content.
Badge
A compact visual indicator for status or category information.

These components are located in components/ui/.

## 6. Feedback Components

Feedback components communicate common interface states.
Component Purpose
LoadingState Indicates an ongoing operation
EmptyState Indicates that no relevant content is available
ErrorState Communicates an error state
SuccessState Communicates successful completion

These components are located in components/feedback/.

## 7. Design Token Guidelines

Use shared tokens from tokens.css instead of introducing unrelated hardcoded values.

When adding or changing styles:

1. Reuse existing tokens where possible.
2. Keep component styles within their component group.
3. Keep global rules in the shared styles directory.
4. Avoid duplicating the same design values across components.
5. Preserve responsive behavior.
6. Use semantic HTML and accessible labels for interactive elements.

## 8. Accessibility Considerations

When building or modifying components:

- Use semantic HTML elements.
- Provide accessible names for interactive controls.
- Preserve keyboard interaction.
- Use appropriate ARIA attributes when necessary.
- Ensure navigation links communicate their destination.
- Do not rely on color alone to communicate important state.

## 9. Extending the Design System

```text
Before creating a new shared component:
1. Check whether an existing component can be reused.
2. Determine whether the behavior is generic or feature-specific.
3. Place generic components under components/ui/ or components/feedback/.
4. Keep feature-specific presentation within the corresponding feature.
5. Add tests for reusable component behavior.

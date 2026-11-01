export interface AppRoute {
    path: string
    label: string
    description: string
    group: 'workspace' | 'resources'
    showInNavigation: boolean
}

export const appRoutes = {
    overview: {
        path: '/',
        label: 'Overview',
        description: 'Platform overview and current workspace status.',
        group: 'workspace',
        showInNavigation: true,
    },
    repositories: {
        path: '/repositories',
        label: 'Repositories',
        description: 'Manage source repositories for evaluation.',
        group: 'workspace',
        showInNavigation: true,
    },
    benchmarks: {
        path: '/benchmarks',
        label: 'Benchmarks',
        description: 'Explore benchmark scenarios and test cases.',
        group: 'workspace',
        showInNavigation: true,
    },
    evaluations: {
        path: '/evaluations',
        label: 'Evaluations',
        description: 'Run and monitor AI repository evaluations.',
        group: 'workspace',
        showInNavigation: true,
    },
    results: {
        path: '/results',
        label: 'Results',
        description: 'Inspect evaluation outcomes and evidence.',
        group: 'workspace',
        showInNavigation: true,
    },
    documentation: {
        path: '/documentation',
        label: 'Documentation',
        description: 'Learn how RepoGuard-Eval works.',
        group: 'resources',
        showInNavigation: true,
    },
    about: {
        path: '/about',
        label: 'About',
        description: 'Learn about the RepoGuard-Eval project.',
        group: 'resources',
        showInNavigation: true,
    },
} satisfies Record<string, AppRoute>

export type AppRouteKey = keyof typeof appRoutes
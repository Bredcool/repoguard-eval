
import type { RouteObject } from 'react-router-dom'

import AppLayout from '../../components/layout/AppLayout'

import OverviewPage from '../../features/overview/pages/OverviewPage'
import RepositoriesPage from '../../features/repositories/pages/RepositoriesPage'
import BenchmarksPage from '../../features/benchmarks/pages/BenchmarksPage'
import EvaluationsPage from '../../features/evaluations/pages/EvaluationsPage'
import ResultsPage from '../../features/results/pages/ResultsPage'
import DocumentationPage from '../../features/documentation/pages/DocumentationPage'
import AboutPage from '../../features/about/pages/AboutPage'

export function NotFoundPage() {
    return (
        <main>
            <h1>404 - Page Not Found</h1>
            <p>The page you are looking for does not exist.</p>
        </main>
    )
}

export const appRouteDefinitions: RouteObject[] = [
    {
        path: '/',
        element: <AppLayout />,
        children: [
            {
                index: true,
                element: <OverviewPage />,
            },
            {
                path: 'repositories',
                element: <RepositoriesPage />,
            },
            {
                path: 'benchmarks',
                element: <BenchmarksPage />,
            },
            {
                path: 'evaluations',
                element: <EvaluationsPage />,
            },
            {
                path: 'results',
                element: <ResultsPage />,
            },
            {
                path: 'documentation',
                element: <DocumentationPage />,
            },
            {
                path: 'about',
                element: <AboutPage />,
            },
        ],
    },
    {
        path: '*',
        element: <NotFoundPage />,
    },
]

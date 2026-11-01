
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import uiReducer from '../../../src/app/store/uiSlice'
import { appRouteDefinitions } from '../../../src/app/router/routeDefinitions'

function renderWithRouter(initialEntry: string) {
    const testStore = configureStore({
        reducer: {
            ui: uiReducer,
        },
    })

    const testRouter = createMemoryRouter(appRouteDefinitions, {
        initialEntries: [initialEntry],
    })

    return {
        ...render(
            <Provider store={testStore}>
                <RouterProvider router={testRouter} />
            </Provider>,
        ),
        router: testRouter,
        store: testStore,
    }
}

describe('Application router', () => {
    it.each([
        ['/', 'RepoGuard-Eval'],
        ['/repositories', 'Repositories'],
        ['/benchmarks', 'Benchmarks'],
        ['/evaluations', 'Evaluations'],
        ['/results', 'Results'],
        ['/documentation', 'Documentation'],
        ['/about', 'About RepoGuard-Eval'],
    ])('renders the correct page at %s', (path, heading) => {
        renderWithRouter(path)

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: heading,
            }),
        ).toBeInTheDocument()
    })

    it('renders the application layout for valid routes', () => {
        renderWithRouter('/repositories')

        expect(
            screen.getByRole('navigation', {
                name: 'Main navigation',
            }),
        ).toBeInTheDocument()

        expect(
            screen.getByRole('banner'),
        ).toBeInTheDocument()
    })

    it('renders the not found page for an unknown route', () => {
        renderWithRouter('/unknown-page')

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: '404 - Page Not Found',
            }),
        ).toBeInTheDocument()
    })

    it('does not render the application sidebar on the not found page', () => {
        renderWithRouter('/unknown-page')

        expect(
            screen.queryByRole('navigation', {
                name: 'Main navigation',
            }),
        ).not.toBeInTheDocument()
    })

    it('navigates from overview to documentation', async () => {
        const user = userEvent.setup()

        renderWithRouter('/')

        await user.click(
            screen.getByRole('button', {
                name: 'View documentation',
            }),
        )

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: 'Documentation',
            }),
        ).toBeInTheDocument()
    })

    it('navigates between pages using the sidebar', async () => {
        const user = userEvent.setup()

        renderWithRouter('/')

        await user.click(
            screen.getByRole('link', {
                name: 'Repositories',
            }),
        )

        expect(
            screen.getByRole('heading', {
                level: 1,
                name: 'Repositories',
            }),
        ).toBeInTheDocument()
    })

    it('marks the current sidebar route as active', () => {
        renderWithRouter('/benchmarks')

        expect(
            screen.getByRole('link', {
                name: 'Benchmarks',
            }),
        ).toHaveClass('sidebar__link--active')
    })
})

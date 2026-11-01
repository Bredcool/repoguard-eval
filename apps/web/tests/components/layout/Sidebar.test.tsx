
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import uiReducer from '../../../src/app/store/uiSlice'
import Sidebar from '../../../src/components/layout/Sidebar'

function renderSidebar(initialCollapsed = false, initialEntry = '/') {
    const testStore = configureStore({
        reducer: {
            ui: uiReducer,
        },
        preloadedState: {
            ui: {
                sidebarCollapsed: initialCollapsed,
            },
        },
    })

    const view = render(
        <Provider store={testStore}>
            <MemoryRouter initialEntries={[initialEntry]}>
                <Sidebar />
            </MemoryRouter>
        </Provider>,
    )

    return {
        ...view,
        store: testStore,
    }
}

describe('Sidebar', () => {
    it('renders the main navigation', () => {
        renderSidebar()

        expect(
            screen.getByRole('navigation', {
                name: 'Main navigation',
            }),
        ).toBeInTheDocument()
    })

    it('renders all workspace navigation links', () => {
        renderSidebar()

        for (const label of [
            'Overview',
            'Repositories',
            'Benchmarks',
            'Evaluations',
            'Results',
        ]) {
            expect(
                screen.getByRole('link', { name: label }),
            ).toBeInTheDocument()
        }
    })

    it('renders all resource navigation links', () => {
        renderSidebar()

        expect(
            screen.getByRole('link', {
                name: 'Documentation',
            }),
        ).toBeInTheDocument()

        expect(
            screen.getByRole('link', {
                name: 'About',
            }),
        ).toBeInTheDocument()
    })

    it('renders the workspace and resources section labels', () => {
        renderSidebar()

        expect(screen.getByText('WORKSPACE')).toBeInTheDocument()
        expect(screen.getByText('RESOURCES')).toBeInTheDocument()
    })

    it('marks the current route as active', () => {
        renderSidebar(false, '/repositories')

        expect(
            screen.getByRole('link', {
                name: 'Repositories',
            }),
        ).toHaveClass('sidebar__link--active')
    })

    it('does not mark unrelated routes as active', () => {
        renderSidebar(false, '/repositories')

        expect(
            screen.getByRole('link', {
                name: 'Benchmarks',
            }),
        ).not.toHaveClass('sidebar__link--active')
    })

    it('renders the expanded brand text when not collapsed', () => {
        renderSidebar(false)

        expect(screen.getByText('RepoGuard')).toBeInTheDocument()
        expect(
            screen.getByText('Evaluation Platform'),
        ).toBeInTheDocument()
    })

    it('hides brand text when collapsed', () => {
        renderSidebar(true)

        expect(screen.queryByText('RepoGuard')).not.toBeInTheDocument()
        expect(
            screen.queryByText('Evaluation Platform'),
        ).not.toBeInTheDocument()
    })

    it('hides navigation labels when collapsed', () => {
        renderSidebar(true)

        expect(
            screen.queryByText('WORKSPACE'),
        ).not.toBeInTheDocument()

        expect(
            screen.queryByText('RESOURCES'),
        ).not.toBeInTheDocument()
    })

    it('preserves accessible titles on collapsed navigation links', () => {
        renderSidebar(true)

        expect(
            screen.getByRole('link', {
                name: 'Repositories',
            }),
        ).toHaveAttribute('title', 'Repositories')
    })

    it('renders the version when expanded', () => {
        renderSidebar(false)

        expect(screen.getByText('Version 1.0.0')).toBeInTheDocument()
    })

    it('hides the version when collapsed', () => {
        renderSidebar(true)

        expect(
            screen.queryByText('Version 1.0.0'),
        ).not.toBeInTheDocument()
    })

    it('applies the collapsed sidebar class', () => {
        const { container } = renderSidebar(true)

        expect(
            container.querySelector('.sidebar'),
        ).toHaveClass('sidebar--collapsed')
    })

    it('does not apply the collapsed class by default', () => {
        const { container } = renderSidebar(false)

        expect(
            container.querySelector('.sidebar'),
        ).not.toHaveClass('sidebar--collapsed')
    })
})

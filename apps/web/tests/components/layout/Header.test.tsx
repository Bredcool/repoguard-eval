
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import uiReducer from '../../../src/app/store/uiSlice'
import Header from '../../../src/components/layout/Header'

function renderHeader(initialCollapsed = false) {
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
            <Header />
        </Provider>,
    )

    return {
        ...view,
        store: testStore,
    }
}

describe('Header', () => {
    it('renders the header', () => {
        renderHeader()

        expect(screen.getByRole('banner')).toBeInTheDocument()
    })

    it('renders the workspace breadcrumb', () => {
        renderHeader()

        expect(screen.getByText('Workspace')).toBeInTheDocument()
        expect(screen.getByText('Overview')).toBeInTheDocument()
    })

    it('renders the development status', () => {
        renderHeader()

        expect(screen.getByText('Development')).toBeInTheDocument()
    })

    it('shows the collapse button when sidebar is expanded', () => {
        renderHeader(false)

        expect(
            screen.getByRole('button', {
                name: 'Collapse sidebar',
            }),
        ).toHaveAttribute('aria-expanded', 'true')
    })

    it('shows the expand button when sidebar is collapsed', () => {
        renderHeader(true)

        expect(
            screen.getByRole('button', {
                name: 'Expand sidebar',
            }),
        ).toHaveAttribute('aria-expanded', 'false')
    })

    it('collapses the sidebar when the button is clicked', async () => {
        const user = userEvent.setup()
        const { store } = renderHeader(false)

        await user.click(
            screen.getByRole('button', {
                name: 'Collapse sidebar',
            }),
        )

        expect(store.getState().ui.sidebarCollapsed).toBe(true)
    })

    it('expands the sidebar when the button is clicked', async () => {
        const user = userEvent.setup()
        const { store } = renderHeader(true)

        await user.click(
            screen.getByRole('button', {
                name: 'Expand sidebar',
            }),
        )

        expect(store.getState().ui.sidebarCollapsed).toBe(false)
    })
})

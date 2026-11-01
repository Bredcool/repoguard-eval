
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import uiReducer from '../../../src/app/store/uiSlice'
import AppLayout from '../../../src/components/layout/AppLayout'

function renderAppLayout() {
    const testStore = configureStore({
        reducer: {
            ui: uiReducer,
        },
    })

    return render(
        <Provider store={testStore}>
            <MemoryRouter>
                <Routes>
                    <Route element={<AppLayout />}>
                        <Route
                            index
                            element={<h1>Test page content</h1>}
                        />
                    </Route>
                </Routes>
            </MemoryRouter>
        </Provider>,
    )
}

describe('AppLayout', () => {
    it('renders the sidebar navigation', () => {
        renderAppLayout()

        expect(
            screen.getByRole('navigation', {
                name: 'Main navigation',
            }),
        ).toBeInTheDocument()
    })

    it('renders the application header', () => {
        renderAppLayout()

        expect(
            screen.getByRole('banner'),
        ).toBeInTheDocument()
    })

    it('renders the nested route content through Outlet', () => {
        renderAppLayout()

        expect(
            screen.getByRole('heading', {
                name: 'Test page content',
            }),
        ).toBeInTheDocument()
    })

    it('renders the main content region', () => {
        renderAppLayout()

        expect(
            screen.getByRole('main'),
        ).toBeInTheDocument()
    })

    it('renders the RepoGuard brand', () => {
        renderAppLayout()

        expect(
            screen.getByText('RepoGuard'),
        ).toBeInTheDocument()
    })
})

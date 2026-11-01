
import { render, screen } from '@testing-library/react'
import { useQueryClient } from '@tanstack/react-query'
import { describe, expect, it } from 'vitest'

import AppProviders from '../../../src/app/providers/AppProviders'
import { useAppSelector } from '../../../src/app/store/hooks'

function ProviderConsumer() {
    const sidebarCollapsed = useAppSelector(
        (state) => state.ui.sidebarCollapsed,
    )

    const queryClient = useQueryClient()

    return (
        <div>
            <span data-testid="sidebar-state">
                {String(sidebarCollapsed)}
            </span>

            <span data-testid="query-client">
                {queryClient ? 'available' : 'unavailable'}
            </span>
        </div>
    )
}

describe('AppProviders', () => {
    it('provides Redux store context to children', () => {
        render(
            <AppProviders>
                <ProviderConsumer />
            </AppProviders>,
        )

        expect(screen.getByTestId('sidebar-state')).toHaveTextContent(
            'false',
        )
    })

    it('provides TanStack Query context to children', () => {
        render(
            <AppProviders>
                <ProviderConsumer />
            </AppProviders>,
        )

        expect(screen.getByTestId('query-client')).toHaveTextContent(
            'available',
        )
    })

    it('renders its children', () => {
        render(
            <AppProviders>
                <p>Provider integration works</p>
            </AppProviders>,
        )

        expect(
            screen.getByText('Provider integration works'),
        ).toBeInTheDocument()
    })
})

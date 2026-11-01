
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ErrorState } from '../../../src/components/feedback'

describe('ErrorState', () => {
    it('renders the default error title', () => {
        render(<ErrorState description="Unable to load repositories." />)

        expect(
            screen.getByRole('heading', {
                name: 'Something went wrong',
            }),
        ).toBeInTheDocument()
    })

    it('renders a custom error title', () => {
        render(
            <ErrorState
                title="Repository loading failed"
                description="Unable to load repositories."
            />,
        )

        expect(
            screen.getByRole('heading', {
                name: 'Repository loading failed',
            }),
        ).toBeInTheDocument()
    })

    it('renders the error description', () => {
        render(
            <ErrorState description="Unable to load repositories." />,
        )

        expect(
            screen.getByText('Unable to load repositories.'),
        ).toBeInTheDocument()
    })

    it('uses the alert role for accessibility', () => {
        render(<ErrorState description="An unexpected error occurred." />)

        expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('applies the error state classes', () => {
        render(<ErrorState description="An unexpected error occurred." />)

        expect(screen.getByRole('alert')).toHaveClass(
            'feedback-state',
            'feedback-state--error',
        )
    })

    it('does not render a retry button when onRetry is omitted', () => {
        render(<ErrorState description="Unable to load repositories." />)

        expect(
            screen.queryByRole('button', { name: 'Try again' }),
        ).not.toBeInTheDocument()
    })

    it('renders the default retry button when onRetry is provided', () => {
        render(
            <ErrorState
                description="Unable to load repositories."
                onRetry={vi.fn()}
            />,
        )

        expect(
            screen.getByRole('button', { name: 'Try again' }),
        ).toBeInTheDocument()
    })

    it('renders a custom retry button label', () => {
        render(
            <ErrorState
                description="Unable to load repositories."
                onRetry={vi.fn()}
                retryLabel="Reload repositories"
            />,
        )

        expect(
            screen.getByRole('button', {
                name: 'Reload repositories',
            }),
        ).toBeInTheDocument()
    })

    it('calls onRetry when the retry button is clicked', async () => {
        const user = userEvent.setup()
        const handleRetry = vi.fn()

        render(
            <ErrorState
                description="Unable to load repositories."
                onRetry={handleRetry}
            />,
        )

        await user.click(
            screen.getByRole('button', { name: 'Try again' }),
        )

        expect(handleRetry).toHaveBeenCalledTimes(1)
    })

    it('uses the secondary button variant for retry', () => {
        render(
            <ErrorState
                description="Unable to load repositories."
                onRetry={vi.fn()}
            />,
        )

        expect(
            screen.getByRole('button', { name: 'Try again' }),
        ).toHaveClass('button--secondary')
    })
})

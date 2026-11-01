
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LoadingState } from '../../../src/components/feedback'

describe('LoadingState', () => {
    it('renders the default loading label', () => {
        render(<LoadingState />)

        expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('renders a custom loading label', () => {
        render(<LoadingState label="Loading repositories..." />)

        expect(
            screen.getByText('Loading repositories...'),
        ).toBeInTheDocument()
    })

    it('uses the status role for accessibility', () => {
        render(<LoadingState />)

        expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('uses polite live announcements', () => {
        render(<LoadingState />)

        expect(screen.getByRole('status')).toHaveAttribute(
            'aria-live',
            'polite',
        )
    })

    it('renders the loading spinner as decorative content', () => {
        render(<LoadingState />)

        const status = screen.getByRole('status')
        const spinner = status.querySelector(
            '.feedback-state__spinner',
        )

        expect(spinner).toBeInTheDocument()
        expect(spinner).toHaveAttribute('aria-hidden', 'true')
    })

    it('applies the loading state classes', () => {
        render(<LoadingState />)

        expect(screen.getByRole('status')).toHaveClass(
            'feedback-state',
            'feedback-state--loading',
        )
    })
})

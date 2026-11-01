
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SuccessState } from '../../../src/components/feedback'

describe('SuccessState', () => {
    it('renders the success title', () => {
        render(<SuccessState title="Repository created" />)

        expect(
            screen.getByRole('heading', {
                name: 'Repository created',
            }),
        ).toBeInTheDocument()
    })

    it('renders the description when provided', () => {
        render(
            <SuccessState
                title="Repository created"
                description="Your repository is ready."
            />,
        )

        expect(
            screen.getByText('Your repository is ready.'),
        ).toBeInTheDocument()
    })

    it('does not render a description when omitted', () => {
        render(<SuccessState title="Repository created" />)

        expect(
            screen.queryByText('Your repository is ready.'),
        ).not.toBeInTheDocument()
    })

    it('uses the status role for accessibility', () => {
        render(<SuccessState title="Repository created" />)

        expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('uses polite live announcements', () => {
        render(<SuccessState title="Repository created" />)

        expect(screen.getByRole('status')).toHaveAttribute(
            'aria-live',
            'polite',
        )
    })

    it('applies the success state classes', () => {
        render(<SuccessState title="Repository created" />)

        expect(screen.getByRole('status')).toHaveClass(
            'feedback-state',
            'feedback-state--success',
        )
    })

    it('renders the decorative success icon', () => {
        const { container } = render(
            <SuccessState title="Repository created" />,
        )

        const icon = container.querySelector(
            '.feedback-state__icon',
        )

        expect(icon).toBeInTheDocument()
        expect(icon).toHaveAttribute('aria-hidden', 'true')
        expect(icon).toHaveTextContent('✓')
    })
})

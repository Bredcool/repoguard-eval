
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EmptyState } from '../../../src/components/feedback'

describe('EmptyState', () => {
    it('renders the title', () => {
        render(<EmptyState title="No repositories found" />)

        expect(
            screen.getByRole('heading', {
                name: 'No repositories found',
            }),
        ).toBeInTheDocument()
    })

    it('renders the description when provided', () => {
        render(
            <EmptyState
                title="No repositories found"
                description="Add a repository to get started."
            />,
        )

        expect(
            screen.getByText('Add a repository to get started.'),
        ).toBeInTheDocument()
    })

    it('does not render a description when omitted', () => {
        render(<EmptyState title="No repositories found" />)

        expect(
            screen.queryByText(/Add a repository/),
        ).not.toBeInTheDocument()
    })

    it('uses the title as the section accessible label', () => {
        render(<EmptyState title="No repositories found" />)

        expect(
            screen.getByRole('region', {
                name: 'No repositories found',
            }),
        ).toBeInTheDocument()
    })

    it('renders the action when provided', () => {
        const handleClick = vi.fn()

        render(
            <EmptyState
                title="No repositories found"
                action={
                    <button type="button" onClick={handleClick}>
                        Add repository
                    </button>
                }
            />,
        )

        expect(
            screen.getByRole('button', {
                name: 'Add repository',
            }),
        ).toBeInTheDocument()
    })

    it('allows the action to be interacted with', async () => {
        const user = userEvent.setup()
        const handleClick = vi.fn()

        render(
            <EmptyState
                title="No repositories found"
                action={
                    <button type="button" onClick={handleClick}>
                        Add repository
                    </button>
                }
            />,
        )

        await user.click(
            screen.getByRole('button', {
                name: 'Add repository',
            }),
        )

        expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not render the action container when action is omitted', () => {
        const { container } = render(
            <EmptyState title="No repositories found" />,
        )

        expect(
            container.querySelector('.feedback-state__action'),
        ).not.toBeInTheDocument()
    })

    it('renders the decorative empty state icon', () => {
        const { container } = render(
            <EmptyState title="No repositories found" />,
        )

        const icon = container.querySelector(
            '.feedback-state__icon',
        )

        expect(icon).toBeInTheDocument()
        expect(icon).toHaveAttribute('aria-hidden', 'true')
        expect(icon).toHaveTextContent('∅')
    })
})

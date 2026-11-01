
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Card } from '../../../src/components/ui'

describe('Card', () => {
    it('renders children correctly', () => {
        render(
            <Card>
                <h2>Repository overview</h2>
                <p>Repository information goes here.</p>
            </Card>,
        )

        expect(
            screen.getByRole('heading', { name: 'Repository overview' }),
        ).toBeInTheDocument()

        expect(
            screen.getByText('Repository information goes here.'),
        ).toBeInTheDocument()
    })

    it('applies the default card class', () => {
        render(<Card>Card content</Card>)

        expect(screen.getByText('Card content')).toHaveClass('card')
    })

    it('supports custom class names', () => {
        render(<Card className="custom-card">Card content</Card>)

        expect(screen.getByText('Card content')).toHaveClass(
            'card',
            'custom-card',
        )
    })

    it('forwards native HTML attributes', () => {
        render(
            <Card data-testid="overview-card" aria-label="Overview">
                Overview content
            </Card>,
        )

        const card = screen.getByTestId('overview-card')

        expect(card).toHaveAttribute('aria-label', 'Overview')
        expect(card).toHaveClass('card')
    })
})

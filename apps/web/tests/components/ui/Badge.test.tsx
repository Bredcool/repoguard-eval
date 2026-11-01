
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge } from '../../../src/components/ui'

describe('Badge', () => {
    it('renders children correctly', () => {
        render(<Badge>Completed</Badge>)

        expect(screen.getByText('Completed')).toBeInTheDocument()
    })

    it('uses neutral as the default variant', () => {
        render(<Badge>Default status</Badge>)

        expect(screen.getByText('Default status')).toHaveClass(
            'badge',
            'badge--neutral',
        )
    })

    it.each([
        ['neutral', 'badge--neutral'],
        ['success', 'badge--success'],
        ['warning', 'badge--warning'],
        ['danger', 'badge--danger'],
        ['info', 'badge--info'],
    ] as const)('applies the %s variant', (variant, expectedClass) => {
        render(<Badge variant={variant}>Status</Badge>)

        expect(screen.getByText('Status')).toHaveClass(
            'badge',
            expectedClass,
        )
    })

    it('supports custom class names', () => {
        render(<Badge className="custom-badge">Active</Badge>)

        expect(screen.getByText('Active')).toHaveClass(
            'badge',
            'badge--neutral',
            'custom-badge',
        )
    })

    it('forwards native HTML attributes', () => {
        render(
            <Badge data-testid="status-badge" title="Evaluation completed">
                Success
            </Badge>,
        )

        const badge = screen.getByTestId('status-badge')

        expect(badge).toHaveAttribute('title', 'Evaluation completed')
    })
})


import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from '../../../src/components/ui'

describe('Button', () => {
    it('renders children correctly', () => {
        render(<Button>Save changes</Button>)

        expect(
            screen.getByRole('button', { name: 'Save changes' }),
        ).toBeInTheDocument()
    })

    it('uses primary and medium as default styles', () => {
        render(<Button>Submit</Button>)

        const button = screen.getByRole('button', { name: 'Submit' })

        expect(button).toHaveClass('button', 'button--primary', 'button--md')
        expect(button).toHaveAttribute('type', 'button')
        expect(button).toHaveAttribute('aria-busy', 'false')
    })

    it.each([
        ['primary', 'button--primary'],
        ['secondary', 'button--secondary'],
        ['danger', 'button--danger'],
    ] as const)('applies the %s variant', (variant, expectedClass) => {
        render(<Button variant={variant}>Action</Button>)

        expect(screen.getByRole('button')).toHaveClass(expectedClass)
    })

    it.each([
        ['sm', 'button--sm'],
        ['md', 'button--md'],
    ] as const)('applies the %s size', (size, expectedClass) => {
        render(<Button size={size}>Action</Button>)

        expect(screen.getByRole('button')).toHaveClass(expectedClass)
    })

    it('calls onClick when clicked', async () => {
        const user = userEvent.setup()
        const handleClick = vi.fn()

        render(<Button onClick={handleClick}>Click me</Button>)

        await user.click(screen.getByRole('button', { name: 'Click me' }))

        expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when disabled', async () => {
        const user = userEvent.setup()
        const handleClick = vi.fn()

        render(
            <Button disabled onClick={handleClick}>
                Disabled action
            </Button>,
        )

        const button = screen.getByRole('button', {
            name: 'Disabled action',
        })

        expect(button).toBeDisabled()

        await user.click(button)

        expect(handleClick).not.toHaveBeenCalled()
    })

    it('disables the button and displays a spinner when loading', () => {
        render(<Button loading>Saving</Button>)

        const button = screen.getByRole('button', { name: 'Saving' })

        expect(button).toBeDisabled()
        expect(button).toHaveAttribute('aria-busy', 'true')
        expect(button.querySelector('.button__spinner')).toBeInTheDocument()
    })

    it('supports custom class names and native button attributes', () => {
        render(
            <Button className="custom-button" type="submit" data-testid="save-button">
                Save
            </Button>,
        )

        const button = screen.getByTestId('save-button')

        expect(button).toHaveClass('custom-button')
        expect(button).toHaveAttribute('type', 'submit')
    })
})

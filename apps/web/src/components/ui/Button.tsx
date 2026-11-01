import type { ButtonHTMLAttributes, ReactNode } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'danger'
export type ButtonSize = 'sm' | 'md'

interface ButtonProps
    extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
    children: ReactNode
    variant?: ButtonVariant
    size?: ButtonSize
    loading?: boolean
}

function Button({
    children,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    className = '',
    type = 'button',
    ...props
}: ButtonProps) {
    const classes = [
        'button',
        `button--${variant}`,
        `button--${size}`,
        className,
    ]
        .filter(Boolean)
        .join(' ')

    return (
        <button
            {...props}
            type={type}
            className={classes}
            disabled={disabled || loading}
            aria-busy={loading}
        >
            {loading && (
                <span className="button__spinner" aria-hidden="true" />
            )}

            <span>{children}</span>
        </button>
    )
}

export default Button
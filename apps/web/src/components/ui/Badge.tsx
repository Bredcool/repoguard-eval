import type { HTMLAttributes, ReactNode } from 'react'

export type BadgeVariant =
    | 'neutral'
    | 'success'
    | 'warning'
    | 'danger'
    | 'info'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    children: ReactNode
    variant?: BadgeVariant
}

function Badge({
    children,
    variant = 'neutral',
    className = '',
    ...props
}: BadgeProps) {
    const classes = [
        'badge',
        `badge--${variant}`,
        className,
    ]
        .filter(Boolean)
        .join(' ')

    return (
        <span {...props} className={classes}>
            {children}
        </span>
    )
}

export default Badge
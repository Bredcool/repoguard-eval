import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    children: ReactNode
}

function Card({
    children,
    className = '',
    ...props
}: CardProps) {
    const classes = ['card', className].filter(Boolean).join(' ')

    return (
        <div {...props} className={classes}>
            {children}
        </div>
    )
}

export default Card
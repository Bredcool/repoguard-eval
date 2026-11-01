import type { ReactNode } from 'react'

interface EmptyStateProps {
    title: string
    description?: string
    action?: ReactNode
}

function EmptyState({
    title,
    description,
    action,
}: EmptyStateProps) {
    return (
        <section className="feedback-state" aria-label={title}>
            <div className="feedback-state__icon" aria-hidden="true">
                ∅
            </div>

            <h2 className="feedback-state__title">{title}</h2>

            {description && (
                <p className="feedback-state__description">
                    {description}
                </p>
            )}

            {action && (
                <div className="feedback-state__action">
                    {action}
                </div>
            )}
        </section>
    )
}

export default EmptyState
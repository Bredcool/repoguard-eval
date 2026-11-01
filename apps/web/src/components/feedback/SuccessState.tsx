interface SuccessStateProps {
    title: string
    description?: string
}

function SuccessState({
    title,
    description,
}: SuccessStateProps) {
    return (
        <section
            className="feedback-state feedback-state--success"
            role="status"
            aria-live="polite"
        >
            <div className="feedback-state__icon" aria-hidden="true">
                ✓
            </div>

            <h2 className="feedback-state__title">{title}</h2>

            {description && (
                <p className="feedback-state__description">
                    {description}
                </p>
            )}
        </section>
    )
}

export default SuccessState
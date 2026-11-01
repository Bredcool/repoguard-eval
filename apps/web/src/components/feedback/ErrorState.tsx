import Button from '../ui/Button'

interface ErrorStateProps {
    title?: string
    description: string
    onRetry?: () => void
    retryLabel?: string
}

function ErrorState({
    title = 'Something went wrong',
    description,
    onRetry,
    retryLabel = 'Try again',
}: ErrorStateProps) {
    return (
        <section
            className="feedback-state feedback-state--error"
            role="alert"
        >
            <div className="feedback-state__icon" aria-hidden="true">
                !
            </div>

            <h2 className="feedback-state__title">{title}</h2>

            <p className="feedback-state__description">
                {description}
            </p>

            {onRetry && (
                <div className="feedback-state__action">
                    <Button variant="secondary" onClick={onRetry}>
                        {retryLabel}
                    </Button>
                </div>
            )}
        </section>
    )
}

export default ErrorState
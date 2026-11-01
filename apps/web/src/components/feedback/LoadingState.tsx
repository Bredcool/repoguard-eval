interface LoadingStateProps {
    label?: string
}

function LoadingState({
    label = 'Loading...',
}: LoadingStateProps) {
    return (
        <div
            className="feedback-state feedback-state--loading"
            role="status"
            aria-live="polite"
        >
            <span className="feedback-state__spinner" aria-hidden="true" />
            <span className="feedback-state__message">{label}</span>
        </div>
    )
}

export default LoadingState
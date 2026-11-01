import EmptyState from '../../../components/feedback/EmptyState'

function EvaluationsPage() {
    return (
        <section>
            <h1>Evaluations</h1>

            <p>
                Run and monitor AI-powered repository debugging evaluations.
            </p>

            <EmptyState
                title="No evaluations yet"
                description="Evaluation execution will be implemented in a future phase."
            />
        </section>
    )
}

export default EvaluationsPage
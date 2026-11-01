import EmptyState from '../../../components/feedback/EmptyState'

function ResultsPage() {
    return (
        <section>
            <h1>Results</h1>

            <p>
                Inspect evaluation outcomes, scores, and supporting evidence.
            </p>

            <EmptyState
                title="No results available"
                description="Evaluation results will appear here once evaluation workflows are implemented."
            />
        </section>
    )
}

export default ResultsPage
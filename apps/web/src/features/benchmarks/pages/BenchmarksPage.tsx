import EmptyState from '../../../components/feedback/EmptyState'

function BenchmarksPage() {
    return (
        <section>
            <h1>Benchmarks</h1>

            <p>
                Explore benchmark scenarios and debugging test cases.
            </p>

            <EmptyState
                title="No benchmarks available"
                description="Benchmark scenarios will be introduced in a future implementation phase."
            />
        </section>
    )
}

export default BenchmarksPage
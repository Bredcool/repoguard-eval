import { Link, useParams } from 'react-router-dom'

import Badge from '../../../components/ui/Badge'
import Card from '../../../components/ui/Card'
import LoadingState from '../../../components/feedback/LoadingState'
import ErrorState from '../../../components/feedback/ErrorState'
import { useExperiment } from '../api/experimentsQueries'

import '../pages/experiments.css'

function ExperimentDetailPage() {
    const { experimentId = '' } = useParams()
    const query = useExperiment(experimentId)

    if (query.isLoading) {
        return <LoadingState label="Loading experiment details..." />
    }

    if (query.isError) {
        return (
            <section className="feature-page">
                <Link className="back-link" to="/experiments">
                    ← Back to experiments
                </Link>
                <ErrorState
                    title="Experiment artifacts unavailable"
                    description={
                        query.error.message.includes('not found')
                            ? 'The experiment definition exists, but its persisted artifact directory is not available yet.'
                            : query.error.message
                    }
                    onRetry={() => void query.refetch()}
                />
            </section>
        )
    }

    const data = query.data
    if (!data) return null

    const { experiment } = data

    return (
        <section className="feature-page">
            <Link className="back-link" to="/experiments">
                ← Back to experiments
            </Link>

            <div className="page-heading">
                <div>
                    <span className="eyebrow">EXPERIMENT DETAIL</span>
                    <h1>{experiment.model || 'Unassigned model'}</h1>
                    <p className="experiment-id">{experiment.experiment_id}</p>
                </div>
                <Badge>{experiment.status || 'Unknown'}</Badge>
            </div>

            <div className="detail-grid">
                <Card className="detail-card">
                    <span className="detail-label">Benchmark</span>
                    <strong>{experiment.benchmark || 'Not specified'}</strong>
                </Card>
                <Card className="detail-card">
                    <span className="detail-label">Provider</span>
                    <strong>{experiment.provider || 'Not specified'}</strong>
                </Card>
                <Card className="detail-card">
                    <span className="detail-label">Total tasks</span>
                    <strong>{experiment.total_tasks ?? 'Not available'}</strong>
                </Card>
            </div>

            <Card className="detail-card">
                <h2>Persisted experiment data</h2>
                <p>
                    The API returned the following source records. Values are
                    displayed as stored; the dashboard does not recalculate scores.
                </p>

                <div className="json-section">
                    <h3>Definition</h3>
                    <pre>{JSON.stringify(data.definition, null, 2)}</pre>
                </div>

                <div className="json-section">
                    <h3>Orchestration metadata</h3>
                    <pre>{JSON.stringify(data.orchestration, null, 2)}</pre>
                </div>

                <div className="json-section">
                    <h3>Result</h3>
                    <pre>{JSON.stringify(data.result, null, 2)}</pre>
                </div>
            </Card>
        </section>
    )
}

export default ExperimentDetailPage

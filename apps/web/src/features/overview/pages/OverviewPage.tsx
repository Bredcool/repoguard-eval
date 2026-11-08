import { Link } from 'react-router-dom'

import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/feedback/EmptyState'
import ErrorState from '../../../components/feedback/ErrorState'
import LoadingState from '../../../components/feedback/LoadingState'
import {
    useApiHealth,
    useExperiments,
} from '../../experiments/api/experimentsQueries'
import type { ExperimentSummary } from '../../experiments/types'

import './overview.css'

function statusVariant(status: string | null) {
    switch (status?.toLowerCase()) {
        case 'completed':
        case 'success':
        case 'passed':
            return 'success' as const
        case 'failed':
        case 'error':
            return 'danger' as const
        case 'running':
        case 'in_progress':
            return 'info' as const
        case 'pending':
        case 'queued':
            return 'warning' as const
        default:
            return 'neutral' as const
    }
}

function MetricCard({
    label,
    value,
    detail,
}: {
    label: string
    value: string | number
    detail: string
}) {
    return (
        <Card className="overview-metric">
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{detail}</small>
        </Card>
    )
}

function RecentExperiment({ experiment }: { experiment: ExperimentSummary }) {
    return (
        <div className="overview-experiment">
            <div className="overview-experiment__main">
                <Link to={`/experiments/${experiment.experiment_id}`}>
                    {experiment.model || experiment.experiment_id}
                </Link>
                <span className="experiment-id">{experiment.experiment_id}</span>
            </div>
            <div className="overview-experiment__meta">
                <span>{experiment.benchmark || 'No benchmark'}</span>
                <Badge variant={statusVariant(experiment.status)}>
                    {experiment.status || 'Unknown'}
                </Badge>
            </div>
        </div>
    )
}

function OverviewPage() {
    const health = useApiHealth()
    const experiments = useExperiments({ limit: 5, offset: 0 })

    const items = experiments.data?.items ?? []
    const total = experiments.data?.pagination.total ?? 0
    const failed = items.filter(
        (item) => item.status?.toLowerCase() === 'failed',
    ).length
    const pending = items.filter(
        (item) => ['pending', 'queued'].includes(item.status?.toLowerCase() || ''),
    ).length
    const completed = items.filter(
        (item) => ['completed', 'success', 'passed'].includes(item.status?.toLowerCase() || ''),
    ).length

    return (
        <main className="overview-page">
            <section className="overview-hero">
                <div>
                    <span className="eyebrow">RESEARCH / EVALUATION PLATFORM</span>
                    <h1>RepoGuard-Eval</h1>
                    <p>
                        Evidence-driven evaluation of AI agents on real
                        repository debugging tasks.
                    </p>
                </div>

                <div className="overview-hero__actions">
                    <Badge variant={health.isSuccess ? 'success' : health.isError ? 'danger' : 'warning'}>
                        <span className="health-indicator" />
                        API {health.isSuccess ? 'Connected' : health.isError ? 'Unavailable' : 'Checking'}
                    </Badge>
                    <Button
                        variant="secondary"
                        onClick={() => {
                            void health.refetch()
                            void experiments.refetch()
                        }}
                        loading={health.isFetching || experiments.isFetching}
                    >
                        Refresh data
                    </Button>
                </div>
            </section>

            {health.isError && (
                <ErrorState
                    title="Dashboard API is unavailable"
                    description="Start the FastAPI service from apps/evaluator and verify the Vite API proxy configuration."
                    onRetry={() => void health.refetch()}
                />
            )}

            {experiments.isLoading ? (
                <LoadingState label="Loading evaluation overview..." />
            ) : experiments.isError ? (
                <ErrorState
                    title="Unable to load experiment data"
                    description={experiments.error.message}
                    onRetry={() => void experiments.refetch()}
                />
            ) : (
                <>
                    <section className="overview-metrics" aria-label="Experiment metrics">
                        <MetricCard
                            label="Total experiments"
                            value={total}
                            detail="Persisted definitions"
                        />
                        <MetricCard
                            label="Completed"
                            value={completed}
                            detail="In current sample"
                        />
                        <MetricCard
                            label="Failed"
                            value={failed}
                            detail="In current sample"
                        />
                        <MetricCard
                            label="Pending"
                            value={pending}
                            detail="In current sample"
                        />
                    </section>

                    <div className="overview-content-grid">
                        <Card className="overview-panel">
                            <div className="overview-panel__heading">
                                <div>
                                    <h2>Recent experiments</h2>
                                    <p>Latest records returned by the API</p>
                                </div>
                                <Link to="/experiments">View all →</Link>
                            </div>

                            {items.length ? (
                                <div className="overview-experiment-list">
                                    {items.map((experiment) => (
                                        <RecentExperiment
                                            key={experiment.experiment_id}
                                            experiment={experiment}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <EmptyState
                                    title="No experiments available"
                                    description="Experiment records will appear here when persisted definitions are discovered by the API."
                                />
                            )}
                        </Card>

                        <Card className="overview-panel overview-integrity">
                            <span className="eyebrow">EVIDENCE FIRST</span>
                            <h2>Execution over assumptions.</h2>
                            <p>
                                RepoGuard-Eval reports persisted evaluator
                                artifacts. Scores and outcomes are not
                                reconstructed by the dashboard.
                            </p>
                            <div className="integrity-item">
                                <span>API service</span>
                                <Badge variant={health.isSuccess ? 'success' : 'warning'}>
                                    {health.isSuccess ? 'Healthy' : 'Unverified'}
                                </Badge>
                            </div>
                            <div className="integrity-item">
                                <span>Model comparison</span>
                                <Badge variant="neutral">No aggregate data</Badge>
                            </div>
                            <div className="integrity-item">
                                <span>Score calculation</span>
                                <Badge variant="success">Backend only</Badge>
                            </div>
                        </Card>
                    </div>
                </>
            )}
        </main>
    )
}

export default OverviewPage

import { useState } from 'react'
import { Link } from 'react-router-dom'

import Badge from '../../../components/ui/Badge'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import LoadingState from '../../../components/feedback/LoadingState'
import EmptyState from '../../../components/feedback/EmptyState'
import ErrorState from '../../../components/feedback/ErrorState'
import { useExperiments } from '../api/experimentsQueries'
import type { ExperimentSummary } from '../types'

import './experiments.css'

const PAGE_SIZE = 10

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

function ExperimentRow({ experiment }: { experiment: ExperimentSummary }) {
    return (
        <tr>
            <td>
                <Link
                    className="experiment-id-link"
                    to={`/experiments/${experiment.experiment_id}`}
                >
                    <span className="experiment-id">
                        {experiment.experiment_id}
                    </span>
                </Link>
            </td>
            <td>
                <Badge variant={statusVariant(experiment.status)}>
                    {experiment.status || 'Unknown'}
                </Badge>
            </td>
            <td>{experiment.model || '—'}</td>
            <td>{experiment.benchmark || '—'}</td>
            <td className="experiment-number">
                {experiment.total_tasks ?? '—'}
            </td>
            <td className="experiment-number">
                {experiment.completed_tasks ?? '—'}
            </td>
            <td className="experiment-number">
                {experiment.failed_tasks ?? '—'}
            </td>
            <td>
                <Link
                    className="table-action-link"
                    to={`/experiments/${experiment.experiment_id}`}
                >
                    Inspect →
                </Link>
            </td>
        </tr>
    )
}

function ExperimentsPage() {
    const [status, setStatus] = useState('')
    const [page, setPage] = useState(0)

    const query = useExperiments({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        status: status || undefined,
    })

    const total = query.data?.pagination.total ?? 0
    const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

    return (
        <section className="feature-page">
            <div className="page-heading">
                <div>
                    <span className="eyebrow">WORKSPACE / EVALUATIONS</span>
                    <h1>Experiments</h1>
                    <p>Browse persisted experiment definitions and evaluation artifacts.</p>
                </div>
                <Button
                    variant="secondary"
                    onClick={() => void query.refetch()}
                    loading={query.isFetching}
                >
                    Refresh
                </Button>
            </div>

            <Card className="experiment-list-card">
                <div className="table-toolbar">
                    <div>
                        <h2>Experiment registry</h2>
                        <p>{total} experiment{total === 1 ? '' : 's'} found</p>
                    </div>

                    <label className="filter-control">
                        <span>Status</span>
                        <select
                            value={status}
                            onChange={(event) => {
                                setStatus(event.target.value)
                                setPage(0)
                            }}
                        >
                            <option value="">All statuses</option>
                            <option value="pending">Pending</option>
                            <option value="running">Running</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                        </select>
                    </label>
                </div>

                {query.isLoading ? (
                    <LoadingState label="Loading experiments..." />
                ) : query.isError ? (
                    <ErrorState
                        title="Unable to load experiments"
                        description={query.error.message}
                        onRetry={() => void query.refetch()}
                    />
                ) : !query.data?.items.length ? (
                    <EmptyState
                        title="No experiments found"
                        description={
                            status
                                ? `No experiments currently match the "${status}" status filter.`
                                : 'No experiment definitions are available in the configured artifact directory.'
                        }
                    />
                ) : (
                    <>
                        <div className="table-scroll">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Experiment ID</th>
                                        <th>Status</th>
                                        <th>Model</th>
                                        <th>Benchmark</th>
                                        <th>Tasks</th>
                                        <th>Completed</th>
                                        <th>Failed</th>
                                        <th aria-label="Actions" />
                                    </tr>
                                </thead>
                                <tbody>
                                    {query.data.items.map((experiment) => (
                                        <ExperimentRow
                                            key={experiment.experiment_id}
                                            experiment={experiment}
                                        />
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="table-pagination">
                            <span>
                                Showing {query.data.pagination.offset + 1}–
                                {Math.min(
                                    query.data.pagination.offset + query.data.items.length,
                                    total,
                                )} of {total}
                            </span>

                            <div>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    disabled={page === 0}
                                    onClick={() => setPage((current) => current - 1)}
                                >
                                    Previous
                                </Button>
                                <span className="pagination-page">
                                    {page + 1} / {pageCount}
                                </span>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    disabled={page + 1 >= pageCount}
                                    onClick={() => setPage((current) => current + 1)}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    </>
                )}
            </Card>
        </section>
    )
}

export default ExperimentsPage

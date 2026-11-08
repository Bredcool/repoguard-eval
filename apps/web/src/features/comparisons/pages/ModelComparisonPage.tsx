import { useState } from 'react'
import { Link } from 'react-router-dom'

import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/feedback/EmptyState'
import ErrorState from '../../../components/feedback/ErrorState'
import LoadingState from '../../../components/feedback/LoadingState'
import { useModelComparisons } from '../../experiments/api/experimentsQueries'

import './comparisons.css'

const PAGE_SIZE = 10

function displayValue(value: number | string | null | undefined): string {
    if (value === null || value === undefined || value === '') {
        return '—'
    }

    return String(value)
}

function ModelComparisonPage() {
    const [benchmark, setBenchmark] = useState('')
    const [page, setPage] = useState(0)

    const query = useModelComparisons({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        benchmark: benchmark || undefined,
    })

    const total = query.data?.pagination.total ?? 0
    const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

    return (
        <section className="feature-page">
            <div className="page-heading">
                <div>
                    <span className="eyebrow">ANALYSIS / MODEL PERFORMANCE</span>
                    <h1>Model Comparison</h1>
                    <p>
                        Compare persisted model evaluation metrics across
                        completed experiment artifacts.
                    </p>
                </div>

                <Button
                    variant="secondary"
                    onClick={() => void query.refetch()}
                    loading={query.isFetching}
                >
                    Refresh
                </Button>
            </div>

            <Card className="comparison-card">
                <div className="table-toolbar">
                    <div>
                        <h2>Comparison registry</h2>
                        <p>
                            {total} comparison{total === 1 ? '' : 's'} available
                        </p>
                    </div>

                    <label className="filter-control">
                        <span>Benchmark</span>
                        <input
                            type="text"
                            value={benchmark}
                            placeholder="Filter benchmark"
                            onChange={(event) => {
                                setBenchmark(event.target.value)
                                setPage(0)
                            }}
                        />
                    </label>
                </div>

                {query.isLoading ? (
                    <LoadingState label="Loading model comparisons..." />
                ) : query.isError ? (
                    <ErrorState
                        title="Unable to load model comparisons"
                        description={query.error.message}
                        onRetry={() => void query.refetch()}
                    />
                ) : !query.data?.items.length ? (
                    <EmptyState
                        title="No comparison artifacts available"
                        description={
                            benchmark
                                ? `No persisted comparisons match benchmark "${benchmark}".`
                                : 'Model comparisons will appear when experiments have persisted aggregate result artifacts.'
                        }
                    />
                ) : (
                    <>
                        <div className="table-scroll">
                            <table className="data-table comparison-table">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Provider</th>
                                        <th>Benchmark</th>
                                        <th>Score</th>
                                        <th>Functional</th>
                                        <th>Build</th>
                                        <th>Regression</th>
                                        <th>Tasks</th>
                                        <th>Generated</th>
                                        <th aria-label="Actions" />
                                    </tr>
                                </thead>
                                <tbody>
                                    {query.data.items.map((item) => (
                                        <tr key={item.experiment_id}>
                                            <td>
                                                <strong className="comparison-model">
                                                    {item.model || 'Unknown model'}
                                                </strong>
                                            </td>
                                            <td>{item.provider || '—'}</td>
                                            <td>
                                                <Badge variant="info">
                                                    {item.benchmark || 'Unknown'}
                                                </Badge>
                                            </td>
                                            <td className="comparison-metric">
                                                {displayValue(item.score)}
                                            </td>
                                            <td className="comparison-metric">
                                                {displayValue(item.functional_pass_rate)}
                                            </td>
                                            <td className="comparison-metric">
                                                {displayValue(item.build_success_rate)}
                                            </td>
                                            <td className="comparison-metric">
                                                {displayValue(item.regression_pass_rate)}
                                            </td>
                                            <td className="comparison-metric">
                                                {displayValue(item.total_tasks)}
                                            </td>
                                            <td>
                                                {item.generated_at
                                                    ? new Date(item.generated_at).toLocaleString()
                                                    : '—'}
                                            </td>
                                            <td>
                                                <Link
                                                    className="table-action-link"
                                                    to={`/experiments/${item.experiment_id}`}
                                                >
                                                    Inspect →
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="table-pagination">
                            <span>
                                Showing {query.data.pagination.offset + 1}–
                                {Math.min(
                                    query.data.pagination.offset +
                                        query.data.items.length,
                                    total,
                                )}{' '}
                                of {total}
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

            <p className="comparison-note">
                Metrics are displayed as returned by the evaluation API.
                The dashboard does not normalize, recalculate, or infer scores.
            </p>
        </section>
    )
}

export default ModelComparisonPage

export interface HealthResponse {
    status: string
    service: string
}

export interface Pagination {
    total: number
    limit: number
    offset: number
}

export interface ExperimentSummary {
    experiment_id: string
    status: string | null
    model: string | null
    provider: string | null
    benchmark: string | null
    total_tasks: number | null
    completed_tasks: number | null
    failed_tasks: number | null
    metadata: Record<string, unknown>
}

export interface ExperimentListResponse {
    items: ExperimentSummary[]
    pagination: Pagination
}

export interface ExperimentDetailResponse {
    experiment: ExperimentSummary
    definition: Record<string, unknown>
    orchestration: Record<string, unknown>
    result: Record<string, unknown>
}

export interface ExperimentListParams {
    limit?: number
    offset?: number
    status?: string
    model?: string
    provider?: string
    benchmark?: string
}

export interface TaskListParams {
    limit?: number
    offset?: number
    status?: string
}

export type TaskResult = Record<string, unknown>

export interface TaskListResponse {
    experiment_id: string
    items: TaskResult[]
    pagination: Pagination
}

export interface ReportResponse {
    experiment_id: string
    metadata: Record<string, unknown>
    aggregate: Record<string, unknown>
    report_markdown: string | null
}

export interface FailureResponse {
    experiment_id: string
    failure_analysis: Record<string, unknown>
}

export interface ModelComparisonItem {
    experiment_id: string
    model: string | null
    provider: string | null
    benchmark: string | null
    score: number | null
    functional_pass_rate: number | null
    build_success_rate: number | null
    regression_pass_rate: number | null
    total_tasks: number | null
    generated_at: string | null
}

export interface ModelComparisonParams {
    limit?: number
    offset?: number
    benchmark?: string
}

export interface ModelComparisonResponse {
    items: ModelComparisonItem[]
    pagination: Pagination
}

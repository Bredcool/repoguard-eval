import type {
    ExperimentDetailResponse,
    ExperimentListParams,
    ExperimentListResponse,
    FailureResponse,
    HealthResponse,
    ModelComparisonParams,
    ModelComparisonResponse,
    ReportResponse,
    TaskListParams,
    TaskListResponse,
} from '../types'

const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL || '/api'
).replace(/\/$/, '')

export class ApiError extends Error {
    status: number
    code: string

    constructor(message: string, status: number, code = 'api_error') {
        super(message)
        this.name = 'ApiError'
        this.status = status
        this.code = code
    }
}

async function parseApiError(response: Response): Promise<ApiError> {
    let message = `API request failed (${response.status}).`
    let code = 'api_error'

    try {
        const body = await response.json() as {
            detail?: string
            error?: string
        }

        message = body.detail || message
        code = body.error || code
    } catch {
        // Preserve the HTTP status message for non-JSON responses.
    }

    return new ApiError(message, response.status, code)
}

async function request<T>(path: string): Promise<T> {
    let response: Response

    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            headers: { Accept: 'application/json' },
        })
    } catch {
        throw new ApiError(
            'Unable to connect to the RepoGuard-Eval API.',
            0,
            'network_error',
        )
    }

    if (!response.ok) {
        throw await parseApiError(response)
    }

    return response.json() as Promise<T>
}

function buildQuery<T extends object>(params: T): string {
    const search = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
            search.set(key, String(value))
        }
    })

    const query = search.toString()
    return query ? `?${query}` : ''
}

function artifactPath(artifactId: string): string {
    const encodedPath = artifactId
        .split('/')
        .map((segment) => encodeURIComponent(segment))
        .join('/')

    return `/artifacts/${encodedPath}`
}

export const experimentsApi = {
    health: () => request<HealthResponse>('/health'),

    list: (params: ExperimentListParams = {}) =>
        request<ExperimentListResponse>(
            `/experiments${buildQuery(params)}`,
        ),

    detail: (experimentId: string) =>
        request<ExperimentDetailResponse>(
            `/experiments/${encodeURIComponent(experimentId)}`,
        ),

    tasks: (
        experimentId: string,
        params: TaskListParams = {},
    ) =>
        request<TaskListResponse>(
            `/experiments/${encodeURIComponent(experimentId)}/tasks${buildQuery(params)}`,
        ),

    report: (experimentId: string) =>
        request<ReportResponse>(
            `/experiments/${encodeURIComponent(experimentId)}/report`,
        ),

    failures: (experimentId: string) =>
        request<FailureResponse>(
            `/experiments/${encodeURIComponent(experimentId)}/failures`,
        ),

    compareModels: (params: ModelComparisonParams = {}) =>
        request<ModelComparisonResponse>(
            `/models/compare${buildQuery(params)}`,
        ),

    downloadArtifact: async (artifactId: string): Promise<Blob> => {
        let response: Response

        try {
            response = await fetch(
                `${API_BASE_URL}${artifactPath(artifactId)}`,
                {
                    headers: { Accept: 'application/octet-stream' },
                },
            )
        } catch {
            throw new ApiError(
                'Unable to connect to the RepoGuard-Eval API.',
                0,
                'network_error',
            )
        }

        if (!response.ok) {
            throw await parseApiError(response)
        }

        return response.blob()
    },
}

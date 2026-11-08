import { useQuery } from '@tanstack/react-query'

import { experimentsApi } from './experimentsApi'
import type {
    ExperimentListParams,
    ModelComparisonParams,
    TaskListParams,
} from '../types'

export const experimentKeys = {
    all: ['experiments'] as const,

    lists: () => [...experimentKeys.all, 'list'] as const,
    list: (params: ExperimentListParams) =>
        [...experimentKeys.lists(), params] as const,

    details: () => [...experimentKeys.all, 'detail'] as const,
    detail: (id: string) =>
        [...experimentKeys.details(), id] as const,

    tasks: (id: string, params: TaskListParams) =>
        [...experimentKeys.all, id, 'tasks', params] as const,

    report: (id: string) =>
        [...experimentKeys.all, id, 'report'] as const,

    failures: (id: string) =>
        [...experimentKeys.all, id, 'failures'] as const,

    comparisons: () =>
        ['model-comparisons'] as const,
    comparison: (params: ModelComparisonParams) =>
        [...experimentKeys.comparisons(), params] as const,

    health: ['system', 'health'] as const,
}

export function useApiHealth() {
    return useQuery({
        queryKey: experimentKeys.health,
        queryFn: experimentsApi.health,
        refetchInterval: 30_000,
    })
}

export function useExperiments(params: ExperimentListParams = {}) {
    return useQuery({
        queryKey: experimentKeys.list(params),
        queryFn: () => experimentsApi.list(params),
    })
}

export function useExperiment(experimentId: string) {
    return useQuery({
        queryKey: experimentKeys.detail(experimentId),
        queryFn: () => experimentsApi.detail(experimentId),
        enabled: Boolean(experimentId),
    })
}

export function useExperimentTasks(
    experimentId: string,
    params: TaskListParams = {},
) {
    return useQuery({
        queryKey: experimentKeys.tasks(experimentId, params),
        queryFn: () => experimentsApi.tasks(experimentId, params),
        enabled: Boolean(experimentId),
    })
}

export function useExperimentReport(experimentId: string) {
    return useQuery({
        queryKey: experimentKeys.report(experimentId),
        queryFn: () => experimentsApi.report(experimentId),
        enabled: Boolean(experimentId),
    })
}

export function useExperimentFailures(experimentId: string) {
    return useQuery({
        queryKey: experimentKeys.failures(experimentId),
        queryFn: () => experimentsApi.failures(experimentId),
        enabled: Boolean(experimentId),
    })
}

export function useModelComparisons(
    params: ModelComparisonParams = {},
) {
    return useQuery({
        queryKey: experimentKeys.comparison(params),
        queryFn: () => experimentsApi.compareModels(params),
    })
}

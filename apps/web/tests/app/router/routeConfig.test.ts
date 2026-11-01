
import { describe, expect, it } from 'vitest'
import { appRoutes } from '../../../src/app/router/routeConfig'

describe('appRoutes', () => {
    it('defines all seven application routes', () => {
        expect(Object.keys(appRoutes)).toHaveLength(7)
    })

    it('defines the expected route paths', () => {
        const paths = Object.values(appRoutes).map(
            (route) => route.path,
        )

        expect(paths).toEqual([
            '/',
            '/repositories',
            '/benchmarks',
            '/evaluations',
            '/results',
            '/documentation',
            '/about',
        ])
    })

    it('assigns workspace routes to the workspace group', () => {
        const workspaceRoutes = Object.values(appRoutes).filter(
            (route) => route.group === 'workspace',
        )

        expect(workspaceRoutes).toHaveLength(5)
        expect(
            workspaceRoutes.map((route) => route.label),
        ).toEqual([
            'Overview',
            'Repositories',
            'Benchmarks',
            'Evaluations',
            'Results',
        ])
    })

    it('assigns resource routes to the resources group', () => {
        const resourceRoutes = Object.values(appRoutes).filter(
            (route) => route.group === 'resources',
        )

        expect(resourceRoutes).toHaveLength(2)
        expect(
            resourceRoutes.map((route) => route.label),
        ).toEqual(['Documentation', 'About'])
    })

    it('makes all defined routes visible in navigation', () => {
        expect(
            Object.values(appRoutes).every(
                (route) => route.showInNavigation,
            ),
        ).toBe(true)
    })

    it('provides a description for every route', () => {
        expect(
            Object.values(appRoutes).every(
                (route) => route.description.trim().length > 0,
            ),
        ).toBe(true)
    })

    it('defines unique paths', () => {
        const paths = Object.values(appRoutes).map(
            (route) => route.path,
        )

        expect(new Set(paths).size).toBe(paths.length)
    })
})

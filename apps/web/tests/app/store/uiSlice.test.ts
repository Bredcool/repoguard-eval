
import { describe, expect, it } from 'vitest'

import uiReducer, {
    toggleSidebar,
    setSidebarCollapsed,
} from '../../../src/app/store/uiSlice'

describe('uiSlice', () => {
    const initialState = {
        sidebarCollapsed: false,
    }

    it('returns the initial state', () => {
        expect(uiReducer(undefined, { type: 'unknown' })).toEqual(
            initialState,
        )
    })

    it('toggles sidebar from expanded to collapsed', () => {
        const nextState = uiReducer(initialState, toggleSidebar())

        expect(nextState.sidebarCollapsed).toBe(true)
    })

    it('toggles sidebar from collapsed to expanded', () => {
        const collapsedState = {
            sidebarCollapsed: true,
        }

        const nextState = uiReducer(
            collapsedState,
            toggleSidebar(),
        )

        expect(nextState.sidebarCollapsed).toBe(false)
    })

    it('sets sidebar collapsed to true', () => {
        const nextState = uiReducer(
            initialState,
            setSidebarCollapsed(true),
        )

        expect(nextState.sidebarCollapsed).toBe(true)
    })

    it('sets sidebar collapsed to false', () => {
        const collapsedState = {
            sidebarCollapsed: true,
        }

        const nextState = uiReducer(
            collapsedState,
            setSidebarCollapsed(false),
        )

        expect(nextState.sidebarCollapsed).toBe(false)
    })

    it('does not mutate the original state', () => {
        const originalState = {
            sidebarCollapsed: false,
        }

        uiReducer(originalState, toggleSidebar())

        expect(originalState.sidebarCollapsed).toBe(false)
    })
})


import { describe, expect, it } from 'vitest'

import { store } from '../../../src/app/store/store'
import {
    toggleSidebar,
    setSidebarCollapsed,
} from '../../../src/app/store/uiSlice'

describe('Redux store', () => {
    it('initializes with the expected UI state', () => {
        expect(store.getState()).toEqual({
            ui: {
                sidebarCollapsed: false,
            },
        })
    })

    it('updates the UI state after dispatching toggleSidebar', () => {
        store.dispatch(toggleSidebar())

        expect(store.getState().ui.sidebarCollapsed).toBe(true)

        store.dispatch(toggleSidebar())

        expect(store.getState().ui.sidebarCollapsed).toBe(false)
    })

    it('updates the UI state after dispatching setSidebarCollapsed', () => {
        store.dispatch(setSidebarCollapsed(true))

        expect(store.getState().ui.sidebarCollapsed).toBe(true)

        store.dispatch(setSidebarCollapsed(false))

        expect(store.getState().ui.sidebarCollapsed).toBe(false)
    })

    it('exposes a dispatch function', () => {
        expect(typeof store.dispatch).toBe('function')
    })

    it('exposes a getState function', () => {
        expect(typeof store.getState).toBe('function')
    })
})

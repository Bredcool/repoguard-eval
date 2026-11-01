import { useAppDispatch, useAppSelector } from '../../app/store/hooks'
import { toggleSidebar } from '../../app/store/uiSlice'

function Header() {
    const dispatch = useAppDispatch()

    const isCollapsed = useAppSelector(
        (state) => state.ui.sidebarCollapsed,
    )

    return (
        <header className="app-header">
            <div className="app-header__left">
                <button
                    type="button"
                    className="app-header__toggle"
                    onClick={() => dispatch(toggleSidebar())}
                    aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    aria-expanded={!isCollapsed}
                >
                    <span aria-hidden="true">☰</span>
                </button>

                <div className="app-header__breadcrumb">
                    <span>Workspace</span>
                    <span className="app-header__separator">/</span>
                    <span className="app-header__current">Overview</span>
                </div>
            </div>

            <div className="app-header__right">
                <span className="app-header__status">
                    <span className="app-header__status-indicator" />
                    Development
                </span>
            </div>
        </header>
    )
}

export default Header
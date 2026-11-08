import { NavLink } from 'react-router-dom'

import { useAppSelector } from '../../app/store/hooks'
import { appRoutes } from '../../app/router/routeConfig'

const workspaceRoutes = Object.values(appRoutes).filter(
    (route) => route.group === 'workspace' && route.showInNavigation,
)

const resourceRoutes = Object.values(appRoutes).filter(
    (route) => route.group === 'resources' && route.showInNavigation,
)

function Sidebar() {
    const isCollapsed = useAppSelector(
        (state) => state.ui.sidebarCollapsed,
    )

    return (
        <aside
            className={`sidebar ${isCollapsed ? 'sidebar--collapsed' : ''}`}
        >
            <div className="sidebar__brand">
                <div className="sidebar__brand-icon">R</div>

                {!isCollapsed && (
                    <div className="sidebar__brand-text">
                        <span className="sidebar__brand-name">RepoGuard</span>
                        <span className="sidebar__brand-caption">
                            Evaluation Platform
                        </span>
                    </div>
                )}
            </div>

            <nav className="sidebar__navigation" aria-label="Main navigation">
                <span className="sidebar__section-label">
                    {!isCollapsed && 'WORKSPACE'}
                </span>

                {workspaceRoutes.map((route) => (
                    <NavLink
                        key={route.path}
                        to={route.path}
                        end={route.path === '/'}
                        className={({ isActive }) =>
                            `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
                        }
                        title={isCollapsed ? route.label : undefined}
                    >
                        <span className="sidebar__link-icon" aria-hidden="true">
                            {route.path === '/' && '◫'}
                            {route.path === '/repositories' && '⌘'}
                            {route.path === '/benchmarks' && '▦'}
                            {route.path === '/evaluations' && '▶'}
                            {route.path === '/experiments' && '◉'}
                            {route.path === '/results' && '▤'}
                            {route.path === '/comparisons' && '⇄'}
                        </span>

                        {!isCollapsed && (
                            <span className="sidebar__link-label">
                                {route.label}
                            </span>
                        )}
                    </NavLink>
                ))}

                <span className="sidebar__section-label sidebar__section-label--resources">
                    {!isCollapsed && 'RESOURCES'}
                </span>

                {resourceRoutes.map((route) => (
                    <NavLink
                        key={route.path}
                        to={route.path}
                        className={({ isActive }) =>
                            `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
                        }
                        title={isCollapsed ? route.label : undefined}
                    >
                        <span className="sidebar__link-icon" aria-hidden="true">
                            {route.path === '/documentation' && '▤'}
                            {route.path === '/about' && 'ⓘ'}
                        </span>

                        {!isCollapsed && (
                            <span className="sidebar__link-label">
                                {route.label}
                            </span>
                        )}
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar__footer">
                {!isCollapsed && (
                    <span className="sidebar__version">Version 1.0.0</span>
                )}
            </div>
        </aside>
    )
}

export default Sidebar
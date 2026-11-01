import { Outlet } from 'react-router-dom'

import Header from './Header'
import Sidebar from './Sidebar'

import './layout.css'

function AppLayout() {
    return (
        <div className="app-layout">
            <Sidebar />

            <div className="app-layout__main">
                <Header />

                <main className="app-layout__content">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}

export default AppLayout
import './styles/tokens.css'
import './styles/reset.css'
import './styles/global.css'
import './styles/utilities.css'

import './components/ui/ui.css'
import './components/feedback/feedback.css'

import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App'
import AppProviders from './app/providers/AppProviders'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <AppProviders>
            <App />
        </AppProviders>
    </React.StrictMode>,
)
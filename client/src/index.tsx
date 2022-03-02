import 'react-app-polyfill/ie11'
import React from 'react'
import ReactDOM from 'react-dom'
import { BrowserRouter as Router } from 'react-router-dom'
import * as Sentry from '@sentry/react'
import { Integrations } from '@sentry/tracing'
import './index.css'
import App from './App'

Sentry.init({
  dsn: (window as any)._arlo_sentry_dsn, // eslint-disable-line @typescript-eslint/no-explicit-any
  environment: (window as any)._arlo_flask_env, // eslint-disable-line @typescript-eslint/no-explicit-any
  integrations: [new Integrations.BrowserTracing()],
  tracesSampleRate: 0.2,
})

ReactDOM.render(
  <Router>
    <App />
  </Router>,
  document.getElementById('root')
)

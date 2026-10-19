import 'react-app-polyfill/ie11'
import React from 'react'
import ReactDOM from 'react-dom'
import { BrowserRouter as Router } from 'react-router-dom'
import * as Sentry from '@sentry/react'
import { Integrations } from '@sentry/tracing'
import { FocusStyleManager } from '@blueprintjs/core'
import './index.css'
import App from './App'

const getMetaContent = (name: string): string | undefined =>
  document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content

if (process.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: getMetaContent('arlo-sentry-dsn'),
    environment: getMetaContent('arlo-flask-env'),
    integrations: [new Integrations.BrowserTracing()],
    tracesSampleRate: 0.2,
  })
}

FocusStyleManager.onlyShowFocusOnTabs()

ReactDOM.render(
  <Router>
    <App />
  </Router>,
  document.getElementById('root')
)

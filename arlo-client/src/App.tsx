import React from 'react'
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import Header from './components/Header'
import AuditForms from './components/AuditForms'
import AuditFlow from './components/AuditFlow'
import CreateAudit from './components/CreateAudit'
import 'react-toastify/dist/ReactToastify.css'
import { useAuth0 } from './react-auth0-spa'
import PrivateRoute from './components/PrivateRoute'

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
`

const App: React.FC = () => {
  const { loading } = useAuth0()
  return (
    <Router>
      <ToastContainer />
      <Main>
        <Route path="/" component={Header} />
        {loading ? (
          <p>loading</p>
        ) : (
          <Switch>
            <PrivateRoute exact path="/" component={CreateAudit} />
            <PrivateRoute
              path="/election/:electionId/board/:token"
              component={AuditFlow}
            />
            <PrivateRoute path="/election/:electionId" component={AuditForms} />
            <PrivateRoute path="/board/:token" component={AuditFlow} />
            <Route>404</Route>
          </Switch>
        )}
      </Main>
    </Router>
  )
}

export default App

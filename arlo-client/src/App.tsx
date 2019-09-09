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

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
`

const App: React.FC = () => {
  return (
    <Router>
      <ToastContainer />
      <Main>
        <Route path="/election" component={Header} />
        <Switch>
          <Route exact path="/" component={CreateAudit} />
          <Route
            path="/election/:electionId/board/:token"
            component={AuditFlow}
          />
          <Route path="/election/:electionId" component={AuditForms} />
          <Route>404</Route>
        </Switch>
      </Main>
    </Router>
  )
}

export default App

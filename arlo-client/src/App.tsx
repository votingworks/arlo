import React from 'react'
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import Header from './components/Header'
import Audit from './components/Audit'
import DataEntry from './components/DataEntry'
import CreateAudit from './components/CreateAudit'
import 'react-toastify/dist/ReactToastify.css'
import AuthDataProvider from './components/UserContext'

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
      <AuthDataProvider>
        <Main>
          <Route path="/" component={Header} />
          <Switch>
            <Route exact path="/" component={CreateAudit} />
            <Route
              path="/election/:electionId/board/:auditBoardId"
              component={DataEntry}
            />
            <Route path="/election/:electionId" component={Audit} />
            <Route>404</Route>
          </Switch>
        </Main>
      </AuthDataProvider>
    </Router>
  )
}

export default App

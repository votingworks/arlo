import React from 'react'
import { BrowserRouter as Router, Route } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import Header from './components/Header'
import AuditForms from './components/AuditForms'
import CreateAudit from './components/CreateAudit'
import 'react-toastify/dist/ReactToastify.css'

const Main = styled.div`
  display: block;
  margin: auto;
  height: 100%;
  overflow: scroll;
  padding: 40px;
  font-size: 1.25rem;
`

const App: React.FC = () => {
  return (
    <Router>
      <ToastContainer />
      <Main>
        {/* eslint-disable react/no-children-prop */}
        <Route
          exact
          path="/"
          children={({ match }) => <Header isHome={!!match} />}
        />
        <Route exact path="/" component={CreateAudit} />
        <Route path="/election/:id" component={AuditForms} />
      </Main>
    </Router>
  )
}

export default App

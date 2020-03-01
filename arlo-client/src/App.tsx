import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import Header from './components/Header'
import AuditForms from './components/AuditForms'
import AuditFlow from './components/AuditFlow'
import CreateAudit, {
  Wrapper as LoadingWrapper,
  Button,
} from './components/CreateAudit'
import 'react-toastify/dist/ReactToastify.css'
import { useAuth0, IAuth0Context } from './react-auth0-spa'
import PrivateRoute from './components/PrivateRoute'
import { api, checkAndToast } from './components/utilities'
import UserContext, { emptyUser } from './UserContext'
import { IUser, IErrorResponse } from './types'

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
`

const App: React.FC = () => {
  const { loading, isAuthenticated } = useAuth0() as IAuth0Context
  const [user, setUser] = useState<IUser>(emptyUser)
  useEffect(() => {
    if (isAuthenticated) {
      ;(async () => {
        const user: IUser | IErrorResponse = await api('/auth/me')
        if ('redirect' in user || checkAndToast(user)) {
          setUser(emptyUser)
          return
        }
        setUser(user)
      })()
    }
  }, [isAuthenticated])

  return (
    <Router>
      <ToastContainer />
      <UserContext.Provider value={user}>
        <Main>
          <Route path="/:election?/:electionId?" component={Header} />
          {loading ? (
            <LoadingWrapper>
              <Button
                type="button"
                intent="primary"
                fill
                large
                loading={loading}
                disabled={loading}
              >
                Loading
              </Button>
            </LoadingWrapper>
          ) : (
            <Switch>
              <Route path="/login">logging in</Route>{' '}
              {/* replace with backend route */}
              <Route exact path="/" component={CreateAudit} />
              <Route
                path="/election/:electionId/board/:token"
                component={AuditFlow}
              />
              <PrivateRoute
                path="/election/:electionId"
                component={AuditForms}
              />
              <Route path="/board/:token" component={AuditFlow} />
              <Route>404</Route>
            </Switch>
          )}
        </Main>
      </UserContext.Provider>
    </Router>
  )
}

export default App

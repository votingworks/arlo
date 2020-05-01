import React, { useContext } from 'react'
import {
  BrowserRouter as Router,
  Route,
  RouteProps,
  Switch,
  Redirect,
} from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import Header from './components/Header'
import Wrapper from './components/Atoms/Wrapper'
import {
  SingleJurisdictionAudit,
  MultiJurisdictionAudit,
} from './components/Audit'
import DataEntry from './components/DataEntry'
import CreateAudit from './components/CreateAudit'
import 'react-toastify/dist/ReactToastify.css'
import AuthDataProvider, { AuthDataContext } from './components/UserContext'
import { IUserMeta } from './types'

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
`

interface PrivateRouteProps extends RouteProps {
  userTypes: IUserMeta['type'][]
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({
  userTypes,
  ...props
}: PrivateRouteProps) => {
  const { isAuthenticated, meta } = useContext(AuthDataContext)
  if (isAuthenticated === null) {
    // Still loading /auth/me, don't show anything
    return <></>
  }
  if (isAuthenticated && userTypes.includes(meta!.type)) {
    return <Route {...props} />
  }
  return (
    <Route
      render={() => (
        <Redirect
          to={{
            pathname: '/',
            state: { from: props.location },
          }}
        />
      )}
    />
  )
}

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
              path="/audit/:electionId"
              component={SingleJurisdictionAudit}
            />
            <PrivateRoute
              userTypes={['audit_board']}
              path="/election/:electionId/board/:auditBoardId"
              component={DataEntry}
            />
            <PrivateRoute
              userTypes={['audit_admin', 'jurisdiction_admin']}
              path="/election/:electionId"
              component={MultiJurisdictionAudit}
            />
            <Route>
              <Wrapper>404 Not Found</Wrapper>
            </Route>
          </Switch>
        </Main>
      </AuthDataProvider>
    </Router>
  )
}

export default App

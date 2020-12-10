import React from 'react'
import { Route, RouteProps, Switch, Redirect } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import Header from './components/Header'
import { Wrapper } from './components/Atoms/Wrapper'
import {
  AuditAdminView,
  JurisdictionAdminView,
} from './components/MultiJurisdictionAudit'
import DataEntry from './components/DataEntry'
import HomeScreen from './components/HomeScreen'
import 'react-toastify/dist/ReactToastify.css'
import AuthDataProvider, {
  IUser,
  useAuthDataContext,
} from './components/UserContext'

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
`

interface PrivateRouteProps extends RouteProps {
  userType: IUser['type']
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({
  userType,
  ...props
}: PrivateRouteProps) => {
  const auth = useAuthDataContext()
  if (auth === null) {
    // Still loading /api/me, don't show anything
    return <></>
  }
  if (auth.user && userType === auth.user.type) {
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
    <>
      <ToastContainer />
      <AuthDataProvider>
        <Main>
          <Route path="/" component={Header} />
          <Switch>
            <Route exact path="/" component={HomeScreen} />
            <PrivateRoute
              userType="audit_board"
              path="/election/:electionId/audit-board/:auditBoardId"
              component={DataEntry}
            />
            <PrivateRoute
              userType="jurisdiction_admin"
              path="/election/:electionId/jurisdiction/:jurisdictionId"
              component={JurisdictionAdminView}
            />
            <PrivateRoute
              userType="audit_admin"
              path="/election/:electionId/:view?"
              component={AuditAdminView}
            />
            <Route>
              <Wrapper>404 Not Found</Wrapper>
            </Route>
          </Switch>
        </Main>
      </AuthDataProvider>
    </>
  )
}

export default App

import React from 'react'
import { Route, RouteProps, Switch, Redirect } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer, toast } from 'react-toastify'
import { QueryClient, QueryClientProvider, DefaultOptions } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
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
import SupportTools from './components/SupportTools'
import ActivityLog from './components/MultiJurisdictionAudit/ActivityLog'
import { ApiError } from './components/SupportTools/support-api'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: ApiError) =>
        // Turn off query retries in test so we can mock effectively
        ['development', 'production'].includes(
          (window as any)._arlo_flask_env // eslint-disable-line @typescript-eslint/no-explicit-any
        ) &&
        error.statusCode >= 500 && // Only retry server errors
        failureCount < 3,
      onError: (error: ApiError) => {
        toast.error(error.message)
      },
    },
    mutations: {
      onError: (error: ApiError) => {
        toast.error(error.message)
      },
    },
  } as DefaultOptions,
})

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
`

interface PrivateRouteProps extends RouteProps {
  userType: IUser['type']
}

export const PrivateRoute: React.FC<PrivateRouteProps> = ({
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
      <QueryClientProvider client={queryClient}>
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
              <PrivateRoute
                userType="audit_admin"
                path="/activity"
                component={ActivityLog}
              />
              <Route path="/support">
                <SupportTools />
              </Route>
              <Route>
                <Wrapper>404 Not Found</Wrapper>
              </Route>
            </Switch>
          </Main>
        </AuthDataProvider>
        {(window as any)._arlo_flask_env === 'development' && ( // eslint-disable-line @typescript-eslint/no-explicit-any
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </>
  )
}

export default App

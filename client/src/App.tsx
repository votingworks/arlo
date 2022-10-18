import React from 'react'
import { Route, RouteProps, Switch, Redirect } from 'react-router-dom'
import './App.css'
import styled from 'styled-components'
import { ToastContainer, toast } from 'react-toastify'
import { QueryClient, QueryClientProvider, DefaultOptions } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
import Header from './components/Header'
import HomeScreen from './components/HomeScreen'
import 'react-toastify/dist/ReactToastify.css'
import AuthDataProvider, {
  IUser,
  useAuthDataContext,
} from './components/UserContext'
import SupportTools from './components/SupportTools'
import JurisdictionAdminView from './components/JurisdictionAdmin/JurisdictionAdminView'
import AuditAdminView from './components/AuditAdmin/AuditAdminView'
import ActivityLog from './components/AuditAdmin/ActivityLog'
import AuditBoardView from './components/AuditBoard/AuditBoardView'
import { ApiError } from './utils/api'
import PublicPages from './components/PublicPages/PublicPages'
import BatchInventory from './components/JurisdictionAdmin/BatchInventory'
import TallyEntryUserView from './components/TallyEntryUser/TallyEntryUserView'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: ApiError) =>
        // Turn off query retries in test so we can mock effectively
        process.env.NODE_ENV !== 'test' &&
        error.statusCode >= 500 && // Only retry server errors
        failureCount < 3,
      onError: (error: ApiError) => {
        toast.error(error.message)
      },
      // When a file input dialog closes, it triggers a window focus event,
      // which causes a refetch by default, so we turn that off to avoid confusion.
      // https://github.com/tannerlinsley/react-query/issues/2960
      refetchOnWindowFocus: false,
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
              <Route exact path="/tally-entry" component={TallyEntryUserView} />
              <PrivateRoute
                userType="audit_board"
                path="/election/:electionId/audit-board/:auditBoardId"
                component={AuditBoardView}
              />
              <PrivateRoute
                userType="jurisdiction_admin"
                path="/election/:electionId/jurisdiction/:jurisdictionId/batch-inventory"
                component={BatchInventory}
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
                <PublicPages />
              </Route>
            </Switch>
          </Main>
        </AuthDataProvider>
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </>
  )
}

export default App

// src/components/PrivateRoute.js

import React, { useEffect } from 'react'
import { Route, RouteProps } from 'react-router-dom'
import { useAuth0, IAuth0Context } from '../react-auth0-spa'

const PrivateRoute = ({ component, path, ...rest }: RouteProps) => {
  const {
    loading,
    isAuthenticated,
    loginWithRedirect,
  } = useAuth0() as IAuth0Context

  useEffect(() => {
    if (loading || isAuthenticated) {
      return
    }
    const fn = async () => {
      await loginWithRedirect({
        appState: { targetUrl: rest.location ? rest.location.pathname : '' },
      })
    }
    fn()
  }, [loading, isAuthenticated, loginWithRedirect, rest.location])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const render = (props: any) =>
    isAuthenticated === true && component
      ? React.createElement(component, props)
      : null // eslint-disable-line no-null/no-null
  return <Route path={path} render={render} {...rest} />
}

export default PrivateRoute

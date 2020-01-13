// src/components/PrivateRoute.js

import React, { useEffect } from 'react'
import { Route } from 'react-router-dom'
import { useAuth0 } from '../react-auth0-spa'

const PrivateRoute = ({ component: Component, path, ...rest }) => {
  const { loading, isAuthenticated, loginWithRedirect } = useAuth0()

  useEffect(() => {
    if (loading || isAuthenticated) {
      return
    }
    const fn = async () => {
      await loginWithRedirect({
        appState: { targetUrl: rest.url },
      })
    }
    fn()
  }, [loading, isAuthenticated, loginWithRedirect, rest.url])

  const render = props =>
    isAuthenticated === true ? <Component {...props} /> : null

  return <Route path={path} render={render} {...rest} />
}

export default PrivateRoute

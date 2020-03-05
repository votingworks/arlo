import React from 'react'
import { Route, RouteProps, Redirect } from 'react-router-dom'
import { useAuthDataContext } from './UserContext'

const PrivateRoute = ({ component, path, ...rest }: RouteProps) => {
  const { isAuthenticated } = useAuthDataContext()

  if (!isAuthenticated) return <Redirect to="/" />
  return <Route path={path} component={component} {...rest} />
}

export default PrivateRoute

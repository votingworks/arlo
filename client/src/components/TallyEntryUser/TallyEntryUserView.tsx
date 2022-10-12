import React from 'react'
import { Switch, Redirect, useRouteMatch, Route } from 'react-router-dom'
import useCurrentUser from './useCurrentUser'
import TallyEntryLoginScreen from './TallyEntryLoginScreen'
import TallyEntryScreen from './TallyEntryScreen'

const TallyEntryUserView: React.FC = () => {
  const { path } = useRouteMatch()
  const userQuery = useCurrentUser()

  if (!userQuery.isSuccess) return null // Still loading

  const user = userQuery.data
  if (user?.type !== 'tally_entry') {
    // TODO figure out when this would happen and handle this case better
    return <Redirect to="/" />
  }

  return (
    <Switch>
      <Route exact path={`${path}/login`}>
        <TallyEntryLoginScreen user={user} />
      </Route>
      {user?.loginConfirmedAt && (
        <Route exact path={path}>
          <TallyEntryScreen />
        </Route>
      )}
      <Redirect to={`${path}/login`} />
    </Switch>
  )
}

export default TallyEntryUserView

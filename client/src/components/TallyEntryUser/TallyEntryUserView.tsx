import React from 'react'
import { Redirect } from 'react-router-dom'
import useCurrentUser from './useCurrentUser'
import TallyEntryLoginScreen from './TallyEntryLoginScreen'
import TallyEntryScreen from './TallyEntryScreen'
import { IUser } from '../UserContext'

const TallyEntryUserView: React.FC = () => {
  const userQuery = useCurrentUser({
    // Once the login code is generated, poll until the login is confirmed
    refetchInterval: (user: IUser | null | undefined) =>
      user?.type === 'tally_entry' &&
      user.loginCode !== null &&
      user.loginConfirmedAt === null
        ? 1000
        : false,
  })

  if (!userQuery.isSuccess) return null // Still loading

  const user = userQuery.data
  if (user?.type !== 'tally_entry') {
    // TODO figure out when this would happen and handle this case better
    return <Redirect to="/" />
  }

  return user.loginConfirmedAt === null ? (
    <TallyEntryLoginScreen user={user} />
  ) : (
    <TallyEntryScreen />
  )
}

export default TallyEntryUserView

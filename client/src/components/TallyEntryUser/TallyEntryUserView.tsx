import React from 'react'
import { H1, Icon, Classes } from '@blueprintjs/core'
import { useLocation } from 'react-router-dom'
import useCurrentUser from './useCurrentUser'
import TallyEntryLoginScreen from './TallyEntryLoginScreen'
import TallyEntryScreen from './TallyEntryScreen'
import { IUser } from '../UserContext'
import { HeaderTallyEntry } from '../Header'
import { Inner } from '../Atoms/Wrapper'
import { Column } from '../Atoms/Layout'

const TallyEntryNotLoggedInScreen: React.FC = () => {
  // Support an 'error' query parameter.
  // We use this to communicate authentication errors to the user.
  const query = new URLSearchParams(useLocation().search)
  const { headline, details } = (() => {
    if (query.get('error') === 'login_link_not_found') {
      return {
        headline: "We couldn't find the login link you entered",
        details:
          'Did you make a typo? Please try entering your login link again.',
      }
    }
    return {
      headline: "You're logged out",
      details: 'To log in, enter your login link in the URL bar.',
    }
  })()

  return (
    <>
      <Inner flexDirection="column">
        <Column alignItems="center" gap="30px" style={{ marginTop: '100px' }}>
          <Icon icon="warning-sign" intent="warning" iconSize={100} />
          <Column alignItems="center" gap="10px">
            <H1>{headline}</H1>
            <p className={Classes.TEXT_LARGE}>{details}</p>
          </Column>
        </Column>
      </Inner>
    </>
  )
}

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
    return <TallyEntryNotLoggedInScreen />
  }

  return (
    <>
      <HeaderTallyEntry />
      {user.loginConfirmedAt === null ? (
        <TallyEntryLoginScreen user={user} />
      ) : (
        <TallyEntryScreen
          electionId={user.electionId}
          jurisdictionId={user.jurisdictionId}
          roundId={user.roundId}
        />
      )}
    </>
  )
}

export default TallyEntryUserView

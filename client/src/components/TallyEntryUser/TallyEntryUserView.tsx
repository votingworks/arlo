import React from 'react'
import { useParams, Switch } from 'react-router-dom'
import { useAuthDataContext } from '../UserContext'
import { assert } from '../utilities'
import useTallyEntryUser from './useTallyEntryUser'

const TallyEntryUserView: React.FC = () => {
  const { jurisdictionId } = useParams<{ jurisdictionId: string }>()
  const tallyEntryUser = useTallyEntryUser()

  // TODO how are we gonna get the audit name/jurisdiction name to display here?
  // - a public endpoint? jurisdictionId -> name
  // - create the tally entry user immediately when they visit the login link
  // - put the jurisdiction id in the session and use that to validate the request for name
  if (tallyEntryUser === null) {
    return <TallyEntryLoginStartScreen jurisdictionId={jurisdictionId} />
  }

  // TODO maybe we want a specific tally entry login error page
  if (tallyEntryUser.jurisdictionId !== jurisdictionId) {
    return <Redirect to="/" />
  }

  if (tallyEntryUser.loginConfirmedAt === null) {
    return <TallyEntryLoginCodeScreen jurisdictionId={jurisdictionId} />
  }

  return <TallyEntryScreen jurisdictionId={jurisdictionId} />
}

export default TallyEntryUserView

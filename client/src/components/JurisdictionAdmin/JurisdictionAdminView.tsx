import React from 'react'
import { useParams } from 'react-router-dom'
import { Wrapper } from '../Atoms/Wrapper'
import useRoundsJurisdictionAdmin from './useRoundsJurisdictionAdmin'
import { isAuditStarted } from '../AuditAdmin/useRoundsAuditAdmin'
import JurisdictionAdminAuditSetup from './JurisdictionAdminAuditSetup'
import RoundManagement from './RoundManagement'
import { useAuthDataContext } from '../UserContext'
import { assert } from '../utilities'

const JurisdictionAdminView: React.FC = () => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const auth = useAuthDataContext()
  const rounds = useRoundsJurisdictionAdmin(electionId, jurisdictionId)

  if (!auth?.user || !rounds) return null

  assert(auth.user.type === 'jurisdiction_admin')
  const jurisdiction = auth.user.jurisdictions.find(
    j => j.id === jurisdictionId
  )!

  if (!isAuditStarted(rounds)) {
    return <JurisdictionAdminAuditSetup jurisdiction={jurisdiction} />
  }
  return (
    <Wrapper>
      <RoundManagement
        jurisdiction={jurisdiction}
        round={rounds[rounds.length - 1]}
      />
    </Wrapper>
  )
}

export default JurisdictionAdminView

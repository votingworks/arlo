import React, { useState, useEffect } from 'react'
import { Redirect, useParams } from 'react-router-dom'
import { ElementType } from '../../types'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import Sidebar from '../Atoms/Sidebar'
import Setup, { setupStages } from './Setup'
import Progress from './Progress'
import useSetupMenuItems from './useSetupMenuItems'
import BallotManifest from './Setup/BallotManifest'
import RoundManagement from './RoundManagement'
import useRoundsJurisdictionAdmin from './useRoundsJurisdictionAdmin'
import { AuditAdminStatusBox, JurisdictionAdminStatusBox } from './StatusBox'
import useBallotManifest from './useBallotManifest'
import useAuditBoards from './useAuditBoards'

interface IParams {
  electionId: string
  view: 'setup' | 'progress' | ''
}

export const AuditAdminView: React.FC = () => {
  const { electionId, view } = useParams<IParams>()
  const [stage, setStage] = useState<ElementType<typeof setupStages>>(
    'Participants'
  )
  const [menuItems, refresh, refreshId] = useSetupMenuItems(
    stage,
    setStage,
    electionId
  )

  useEffect(() => {
    refresh()
  }, [refresh])

  switch (view) {
    case 'setup':
      return (
        <Wrapper>
          <AuditAdminStatusBox refreshId={refreshId} />
          <Inner>
            <Sidebar title="Audit Setup" menuItems={menuItems} />
            <Setup stage={stage} refresh={refresh} menuItems={menuItems} />
          </Inner>
        </Wrapper>
      )
    case 'progress':
      return (
        <Wrapper>
          <AuditAdminStatusBox refreshId={refreshId} />
          <Inner>
            <Sidebar
              title="Audit Progress"
              menuItems={[
                {
                  title: 'Jurisdictions',
                  active: true,
                  state: 'live',
                },
              ]}
            />
            <Progress refreshId={refreshId} />
          </Inner>
        </Wrapper>
      )
    default:
      return <Redirect to={`/election/${electionId}/progress`} />
  }
}

export const JurisdictionAdminView: React.FC = () => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  const rounds = useRoundsJurisdictionAdmin(electionId, jurisdictionId)
  const [
    ballotManifest,
    uploadBallotManifest,
    deleteBallotManifest,
  ] = useBallotManifest(electionId, jurisdictionId)
  const [auditBoards, createAuditBoards] = useAuditBoards(
    electionId,
    jurisdictionId,
    rounds
  )

  if (!rounds || !ballotManifest || !auditBoards) return null // Still loading
  if (!rounds.length) {
    return (
      <Wrapper>
        <JurisdictionAdminStatusBox
          rounds={rounds}
          ballotManifest={ballotManifest}
          auditBoards={auditBoards}
        />
        <Inner>
          <BallotManifest
            ballotManifest={ballotManifest}
            uploadBallotManifest={uploadBallotManifest}
            deleteBallotManifest={deleteBallotManifest}
          />
        </Inner>
      </Wrapper>
    )
  }
  return (
    <Wrapper>
      <JurisdictionAdminStatusBox
        rounds={rounds}
        ballotManifest={ballotManifest}
        auditBoards={auditBoards}
      />
      <Inner>
        <RoundManagement
          round={rounds[rounds.length - 1]}
          auditBoards={auditBoards}
          createAuditBoards={createAuditBoards}
        />
      </Inner>
    </Wrapper>
  )
}

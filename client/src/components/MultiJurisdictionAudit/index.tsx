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
import {
  AuditAdminStatusBox,
  JurisdictionAdminStatusBox,
  isSetupComplete,
} from './StatusBox'
import { useBallotManifest, useBatchTallies } from './useCSV'
import useAuditBoards from './useAuditBoards'
import useAuditSettings from './useAuditSettings'
import useJurisdictions, { FileProcessingStatus } from './useJurisdictions'
import useContests from './useContests'
import useRoundsAuditAdmin from './useRoundsAuditAdmin'
import BatchTallies from './Setup/BatchTallies'

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

  const rounds = useRoundsAuditAdmin(electionId, refreshId)
  const jurisdictions = useJurisdictions(electionId, refreshId)
  const [contests] = useContests(electionId, refreshId)
  const [auditSettings] = useAuditSettings(electionId, refreshId)

  useEffect(() => {
    refresh()
  }, [refresh])

  if (!contests || !rounds) return null // Still loading

  switch (view) {
    case 'setup':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            jurisdictions={jurisdictions}
            contests={contests}
            auditSettings={auditSettings}
          />
          <Inner>
            <Sidebar title="Audit Setup" menuItems={menuItems} />
            <Setup stage={stage} refresh={refresh} menuItems={menuItems} />
          </Inner>
        </Wrapper>
      )
    case 'progress':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            jurisdictions={jurisdictions}
            contests={contests}
            auditSettings={auditSettings}
          />
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
            <Progress jurisdictions={jurisdictions} />
          </Inner>
        </Wrapper>
      )
    default:
      return (
        <Redirect
          to={
            isSetupComplete(jurisdictions, contests, auditSettings)
              ? `/election/${electionId}/progress`
              : `/election/${electionId}/setup`
          }
        />
      )
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
  const [
    batchTallies,
    uploadBatchTallies,
    deleteBatchTallies,
  ] = useBatchTallies(electionId, jurisdictionId)
  const [auditBoards, createAuditBoards] = useAuditBoards(
    electionId,
    jurisdictionId,
    rounds
  )

  if (!rounds || !ballotManifest || !batchTallies || !auditBoards) return null // Still loading
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
          {ballotManifest.processing &&
            ballotManifest.processing.status ===
              FileProcessingStatus.PROCESSED && (
              <BatchTallies
                batchTallies={batchTallies}
                uploadBatchTallies={uploadBatchTallies}
                deleteBatchTallies={deleteBatchTallies}
              />
            )}
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

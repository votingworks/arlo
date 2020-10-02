import React, { useEffect, useState } from 'react'
import { Redirect, useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Tag } from '@blueprintjs/core'
import { ElementType } from '../../types'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import Sidebar from '../Atoms/Sidebar'
import Setup, { setupStages } from './AASetup'
import Progress from './Progress'
import useSetupMenuItems from './useSetupMenuItems'
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
import useAuditSettingsJurisdictionAdmin from './RoundManagement/useAuditSettingsJurisdictionAdmin'
import H2Title from '../Atoms/H2Title'
import CSVFile from './CSVForm'
import { useInterval } from '../utilities'

const VerticalInner = styled(Inner)`
  flex-direction: column;
`

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

  useEffect(refresh, [refresh])

  if (!contests || !rounds || !auditSettings) return null // Still loading

  // TODO support multiple contests in batch comparison audits
  const isBatch = auditSettings.auditType === 'BATCH_COMPARISON'
  const isBallotComparison = auditSettings.auditType === 'BALLOT_COMPARISON'
  const filteredMenuItems = menuItems.filter(({ title }) => {
    switch (title as ElementType<typeof setupStages>) {
      case 'Opportunistic Contests':
        return !isBatch
      case 'Participants':
        return !isBallotComparison
      case 'Participants & Contests':
        return !!isBallotComparison
      default:
        return true
    }
  })

  if (isBallotComparison && stage === 'Participants')
    setStage('Participants & Contests')

  switch (view) {
    case 'setup':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            jurisdictions={jurisdictions}
            contests={contests}
            auditSettings={auditSettings}
          >
            <RefreshTag refresh={refresh} />
          </AuditAdminStatusBox>
          <Inner>
            <Sidebar title="Audit Setup" menuItems={filteredMenuItems} />
            <Setup
              stage={stage}
              refresh={refresh}
              menuItems={menuItems}
              auditType={auditSettings.auditType}
            />
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
          >
            <RefreshTag refresh={refresh} />
          </AuditAdminStatusBox>
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
            <Progress
              jurisdictions={jurisdictions}
              auditSettings={auditSettings}
              round={rounds[rounds.length - 1]}
            />
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

  const auditSettings = useAuditSettingsJurisdictionAdmin(
    electionId,
    jurisdictionId
  )
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

  if (
    !rounds ||
    !ballotManifest ||
    !batchTallies ||
    !auditBoards ||
    !auditSettings
  )
    return null // Still loading

  if (!rounds.length) {
    return (
      <Wrapper>
        <JurisdictionAdminStatusBox
          rounds={rounds}
          ballotManifest={ballotManifest}
          auditBoards={auditBoards}
        />
        <VerticalInner>
          <H2Title>Audit Source Data</H2Title>
          <CSVFile
            csvFile={ballotManifest}
            uploadCSVFile={uploadBallotManifest}
            deleteCSVFile={deleteBallotManifest}
            filePurpose="ballot-manifest"
            enabled
          />
          {auditSettings.auditType === 'BATCH_COMPARISON' && (
            <CSVFile
              csvFile={batchTallies}
              enabled={
                !!ballotManifest.processing &&
                ballotManifest.processing.status ===
                  FileProcessingStatus.PROCESSED
              }
              uploadCSVFile={uploadBatchTallies}
              deleteCSVFile={deleteBatchTallies}
              filePurpose="batch-tallies"
            />
          )}
        </VerticalInner>
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

const RefreshStatusTag = styled(Tag)`
  margin-top: 20px;
  width: 14em;
  text-align: center;
`

export const prettifyRefreshStatus = (refreshTime: number) => {
  if (refreshTime < 240000)
    return `Will refresh in ${5 - Math.floor(refreshTime / 60000)} minutes`
  if (refreshTime < 250000) return `Will refresh in 1 minute`
  return `Will refresh in ${Math.ceil((300000 - refreshTime) / 10000) *
    10} seconds`
}

const RefreshTag = ({ refresh }: { refresh: () => void }) => {
  const [lastRefreshTime, setLastRefreshTime] = useState(Date.now())
  const [time, setTime] = useState(Date.now())

  // poll the apis every 5 minutes
  useInterval(() => {
    const now = Date.now()
    if (now - lastRefreshTime >= 1000 * 60 * 5) {
      setLastRefreshTime(now)
      refresh()
    }
    setTime(now)
  }, 1000)

  return (
    <RefreshStatusTag>
      {prettifyRefreshStatus(time - lastRefreshTime)}
    </RefreshStatusTag>
  )
}

import React, { useState } from 'react'
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

export const prettifyRefreshStatus = (refreshTime: number) => {
  if (refreshTime < 10000) return 'Refreshed just now'
  if (refreshTime < 60000)
    return `Refreshed ${Math.floor(refreshTime / 10000) * 10} seconds ago`
  if (refreshTime < 120000) return `Refreshed 1 minute ago`
  return `Refreshed ${Math.floor(refreshTime / 60000)} minutes ago`
}

const VerticalInner = styled(Inner)`
  flex-direction: column;
`

const RefreshStatusTag = styled(Tag)`
  margin-top: 20px;
  width: 20em;
  text-align: center;
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

  const [refreshTime, setRefreshTime] = useState(0)
  const incrementRefreshTime = () => setRefreshTime(refreshTime + 1000)

  // poll the apis every 5 minutes
  useInterval(
    () => {
      setRefreshTime(0)
      refresh()
    },
    300000,
    true
  )
  // update the refresh time tracker every second
  useInterval(incrementRefreshTime, 1000, false)
  const refreshStatus = prettifyRefreshStatus(refreshTime)

  // TODO support multiple contests in batch comparison audits
  const isBatch = auditSettings.auditType === 'BATCH_COMPARISON'
  const singleContestMenuItems = menuItems.filter(
    i => i.title !== 'Opportunistic Contests'
  )

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
          >
            <RefreshStatusTag>{refreshStatus}</RefreshStatusTag>
          </AuditAdminStatusBox>
          <Inner>
            <Sidebar
              title="Audit Setup"
              menuItems={isBatch ? singleContestMenuItems : menuItems}
            />
            <Setup
              stage={stage}
              refresh={refresh}
              menuItems={menuItems}
              isBatch={isBatch}
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
            <RefreshStatusTag>{refreshStatus}</RefreshStatusTag>
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

  const { auditType } = useAuditSettingsJurisdictionAdmin(
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

  if (!rounds || !ballotManifest || !batchTallies || !auditBoards) return null // Still loading
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
          {auditType === 'BATCH_COMPARISON' && (
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

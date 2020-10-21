import React, { useEffect, useState } from 'react'
import { Redirect, useParams } from 'react-router-dom'
import styled from 'styled-components'
import uuidv4 from 'uuidv4'
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
import { useBallotManifest, useBatchTallies, useCVRS } from './useCSV'
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
  const [refreshId, setRefreshId] = useState(uuidv4())

  const rounds = useRoundsAuditAdmin(electionId, refreshId)
  const jurisdictions = useJurisdictions(electionId, refreshId)
  const [contests] = useContests(electionId, refreshId)
  const [auditSettings] = useAuditSettings(electionId, refreshId)

  const isBallotComparison =
    auditSettings && auditSettings.auditType === 'BALLOT_COMPARISON'
  const [stage, setStage] = useState<ElementType<typeof setupStages>>(
    'participants'
  )
  const [menuItems, refresh] = useSetupMenuItems(
    stage,
    setStage,
    electionId,
    !!isBallotComparison,
    setRefreshId
  )

  useEffect(refresh, [refresh, isBallotComparison])

  if (!contests || !rounds || !auditSettings) return null // Still loading

  // TODO support multiple contests in batch comparison audits
  const isBatch = auditSettings.auditType === 'BATCH_COMPARISON'
  const filteredMenuItems = menuItems.filter(({ id }) => {
    switch (id as ElementType<typeof setupStages>) {
      case 'opportunistic-contests':
        return !isBatch
      default:
        return true
    }
  })

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
                  id: 'jurisdictions',
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
  const [cvrs, uploadCVRS, deleteCVRS] = useCVRS(electionId, jurisdictionId)
  const [auditBoards, createAuditBoards] = useAuditBoards(
    electionId,
    jurisdictionId,
    rounds
  )

  if (
    !rounds ||
    !ballotManifest ||
    !batchTallies ||
    !cvrs ||
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
            title="Ballot Manifest"
            description='Click "Browse" to choose the appropriate Ballot
                  Manifest file from your computer. This file should be a
                  comma-separated list of all the ballot boxes/containers used
                  to store ballots for this particular election, plus a count of
                  how many ballot cards (individual pieces of paper) are stored
                  in each container.'
            sampleFileLink="/sample_ballot_manifest.csv"
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
              title="Candidate Totals by Batch"
              description='Click "Browse" to choose the appropriate Candidate
                  Totals by Batch file from your computer. This file should be a
                  comma-separated list of all the ballot boxes/containers used
                  to store ballots for this particular election, plus a count of
                  how many votes were counted for each candidate in each of
                  those containers.'
              sampleFileLink="/sample_candidate_totals_by_batch.csv"
            />
          )}
          {auditSettings.auditType === 'BALLOT_COMPARISON' && (
            <CSVFile
              csvFile={cvrs}
              enabled={
                !!ballotManifest.processing &&
                ballotManifest.processing.status ===
                  FileProcessingStatus.PROCESSED
              }
              uploadCSVFile={uploadCVRS}
              deleteCSVFile={deleteCVRS}
              title="Cast Vote Records"
              description='Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file from your computer. This file should be a
                  comma-separated list of all the ballots counted by your
                  tabulator, in order.'
              sampleFileLink=""
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

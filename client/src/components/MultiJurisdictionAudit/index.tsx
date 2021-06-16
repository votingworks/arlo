import React, { useEffect, useState } from 'react'
import { Redirect, useParams } from 'react-router-dom'
import styled from 'styled-components'
import uuidv4 from 'uuidv4'
import { Tag, Spinner, H3, Intent } from '@blueprintjs/core'
import { ElementType } from '../../types'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import Sidebar from '../Atoms/Sidebar'
import Setup, { setupStages } from './AASetup'
import Progress from './Progress'
import useSetupMenuItems from './useSetupMenuItems'
import RoundManagement from './RoundManagement'
import useRoundsJurisdictionAdmin from './useRoundsJurisdictionAdmin'
import { AuditAdminStatusBox, JurisdictionAdminStatusBox } from './StatusBox'
import {
  useBallotManifest,
  useBatchTallies,
  useCVRs,
  FileProcessingStatus,
} from './useCSV'
import useAuditBoards from './useAuditBoards'
import useAuditSettings from './useAuditSettings'
import useJurisdictions from './useJurisdictions'
import useContests from './useContests'
import useRoundsAuditAdmin, {
  isDrawSampleComplete,
  drawSampleError,
  isAuditStarted,
} from './useRoundsAuditAdmin'
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

  const [rounds, startNextRound, undoRoundStart] = useRoundsAuditAdmin(
    electionId,
    refreshId
  )
  const jurisdictions = useJurisdictions(electionId, refreshId)
  const [contests] = useContests(electionId, undefined, refreshId)
  const [auditSettings] = useAuditSettings(electionId, refreshId)

  const isBallotComparison =
    auditSettings !== null && auditSettings.auditType === 'BALLOT_COMPARISON'
  const isHybrid =
    auditSettings !== null && auditSettings.auditType === 'HYBRID'
  const [stage, setStage] = useState<ElementType<typeof setupStages>>(
    'participants'
  )
  const [menuItems, refresh] = useSetupMenuItems(
    stage,
    setStage,
    electionId,
    !!isBallotComparison,
    !!isHybrid,
    setRefreshId
  )

  useEffect(refresh, [
    refresh,
    isBallotComparison,
    isHybrid,
    rounds !== null && isAuditStarted(rounds),
  ])

  if (!jurisdictions || !contests || !rounds || !auditSettings) return null // Still loading

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

  if (rounds.length > 0 && !isDrawSampleComplete(rounds)) {
    return (
      <Wrapper>
        <Inner>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              marginTop: '100px',
            }}
          >
            <div style={{ marginBottom: '20px' }}>
              <Spinner size={Spinner.SIZE_LARGE} intent={Intent.PRIMARY} />
            </div>
            <H3>Drawing a random sample of ballots...</H3>
            <p>For large elections, this can take a couple of minutes.</p>
          </div>
        </Inner>
      </Wrapper>
    )
  }

  switch (view) {
    case 'setup':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            startNextRound={startNextRound}
            undoRoundStart={undoRoundStart}
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
              startNextRound={startNextRound}
            />
          </Inner>
        </Wrapper>
      )
    case 'progress':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            startNextRound={startNextRound}
            undoRoundStart={undoRoundStart}
            jurisdictions={jurisdictions}
            contests={contests}
            auditSettings={auditSettings}
          >
            <RefreshTag refresh={refresh} />
          </AuditAdminStatusBox>
          {!drawSampleError(rounds) && (
            <Inner>
              <Progress
                jurisdictions={jurisdictions}
                auditSettings={auditSettings}
                round={rounds[rounds.length - 1]}
              />
            </Inner>
          )}
        </Wrapper>
      )
    default:
      return (
        <Redirect
          to={
            rounds.length > 0
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
  const [cvrs, uploadCVRS, deleteCVRS] = useCVRs(electionId, jurisdictionId)
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

  if (!isAuditStarted(rounds)) {
    return (
      <Wrapper>
        <JurisdictionAdminStatusBox
          rounds={rounds}
          ballotManifest={ballotManifest}
          batchTallies={batchTallies}
          cvrs={cvrs}
          auditBoards={auditBoards}
          auditType={auditSettings.auditType}
          auditName={auditSettings.auditName}
        />
        <VerticalInner>
          <H2Title>Audit Source Data</H2Title>
          <CSVFile
            csvFile={ballotManifest}
            uploadCSVFile={uploadBallotManifest}
            deleteCSVFile={deleteBallotManifest}
            title={
              auditSettings.auditType === 'HYBRID'
                ? 'Ballot Manifest (All ballots)'
                : 'Ballot Manifest'
            }
            description={
              auditSettings.auditType === 'HYBRID'
                ? `Click "Browse" to choose the appropriate Ballot
                  Manifest file from your computer. This file should be a
                  comma-separated list of all the ballot batches/containers used
                  to store ballots for this particular election, plus a count of
                  how many ballot cards (individual pieces of paper) are stored
                  in each container, and whether each batch has cast vote records.`
                : `Click "Browse" to choose the appropriate Ballot
                Manifest file from your computer. This file should be a
                comma-separated list of all the ballot boxes/containers used
                to store ballots for this particular election, plus a count of
                how many ballot cards (individual pieces of paper) are stored
                in each container.`
            }
            sampleFileLink={(type => {
              switch (type) {
                case 'BALLOT_COMPARISON':
                  return '/sample_manifest_BC.csv'
                case 'HYBRID':
                  return '/sample_manifest_hybrid.csv'
                default:
                  return '/sample_ballot_manifest.csv'
              }
            })(auditSettings.auditType)}
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
          {['BALLOT_COMPARISON', 'HYBRID'].includes(
            auditSettings.auditType
          ) && (
            <CSVFile
              csvFile={cvrs}
              enabled={
                !!ballotManifest.processing &&
                ballotManifest.processing.status ===
                  FileProcessingStatus.PROCESSED
              }
              uploadCSVFile={uploadCVRS}
              deleteCSVFile={deleteCVRS}
              title={
                auditSettings.auditType === 'HYBRID'
                  ? 'Cast Vote Records (CVR ballots only)'
                  : 'Cast Vote Records'
              }
              description={
                auditSettings.auditType === 'HYBRID'
                  ? `Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file from your computer. This file should be a
                  comma-separated list (.csv) of all the ballots centrally counted by your
                  tabulator(s), but should not include precinct-count ballots.`
                  : `Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file from your computer. This file should be a
                  comma-separated list (.csv) of all the ballots counted by your
                  tabulator(s), in order.`
              }
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
        batchTallies={batchTallies}
        cvrs={cvrs}
        auditBoards={auditBoards}
        auditType={auditSettings.auditType}
        auditName={auditSettings.auditName}
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

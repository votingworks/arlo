import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import useRoundsJurisdictionAdmin from './useRoundsJurisdictionAdmin'
import { JurisdictionAdminStatusBox } from '../Atoms/StatusBox'
import {
  useBallotManifest,
  useBatchTallies,
  useCVRs,
  FileProcessingStatus,
} from '../useCSV'
import useAuditBoards from '../useAuditBoards'
import useAuditSettingsJurisdictionAdmin from './useAuditSettingsJurisdictionAdmin'
import H2Title from '../Atoms/H2Title'
import CSVFile from '../Atoms/CSVForm'
import { isAuditStarted } from '../AuditAdmin/useRoundsAuditAdmin'
import RoundManagement from './RoundManagement'

const VerticalInner = styled(Inner)`
  flex-direction: column;
`

const JurisdictionAdminView: React.FC = () => {
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
  ] = useBatchTallies(electionId, jurisdictionId, auditSettings, ballotManifest)
  const [cvrs, uploadCVRS, deleteCVRS] = useCVRs(
    electionId,
    jurisdictionId,
    auditSettings,
    ballotManifest
  )
  const [auditBoards, createAuditBoards] = useAuditBoards(
    electionId,
    jurisdictionId,
    rounds
  )
  const isBatchComparison =
    auditSettings && auditSettings.auditType === 'BATCH_COMPARISON'
  const isBallotComparison =
    auditSettings && auditSettings.auditType === 'BALLOT_COMPARISON'
  const isHybrid = auditSettings && auditSettings.auditType === 'HYBRID'

  if (
    !rounds ||
    !ballotManifest ||
    (isBatchComparison && !batchTallies) ||
    ((isBallotComparison || isHybrid) && !cvrs) ||
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
          isAuditOnline={!!auditSettings.online}
        />
        <VerticalInner>
          <H2Title>Audit Source Data</H2Title>
          <CSVFile
            csvFile={ballotManifest}
            uploadCSVFiles={uploadBallotManifest}
            deleteCSVFile={deleteBallotManifest}
            title={
              isHybrid ? 'Ballot Manifest (All ballots)' : 'Ballot Manifest'
            }
            description={
              isHybrid
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
          {isBatchComparison && (
            <CSVFile
              csvFile={batchTallies!}
              enabled={
                !!ballotManifest.processing &&
                ballotManifest.processing.status ===
                  FileProcessingStatus.PROCESSED
              }
              uploadCSVFiles={uploadBatchTallies}
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
          {(isBallotComparison || isHybrid) && (
            <CSVFile
              csvFile={cvrs!}
              enabled={
                !!ballotManifest.processing &&
                ballotManifest.processing.status ===
                  FileProcessingStatus.PROCESSED
              }
              uploadCSVFiles={uploadCVRS}
              deleteCSVFile={deleteCVRS}
              title={
                isHybrid
                  ? 'Cast Vote Records (CVR ballots only)'
                  : 'Cast Vote Records'
              }
              description={
                isHybrid
                  ? `Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file from your computer. This file should be an export
                  of all the ballots centrally counted by your tabulator(s),
                  but should not include precinct-count ballots.`
                  : `Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file from your computer. This file should be an export
                  of all the ballots counted by your tabulator(s).`
              }
              showCvrFileType
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
        isAuditOnline={!!auditSettings.online}
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

export default JurisdictionAdminView

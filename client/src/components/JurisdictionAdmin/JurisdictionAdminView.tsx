import React from 'react'
import { useParams } from 'react-router-dom'
import { H4, Card, Callout } from '@blueprintjs/core'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import useRoundsJurisdictionAdmin from './useRoundsJurisdictionAdmin'
import {
  useBallotManifest,
  useBatchTallies,
  useCVRs,
  FileProcessingStatus,
  isFileProcessed,
} from '../useCSV'
import useAuditBoards from '../useAuditBoards'
import useAuditSettingsJurisdictionAdmin from './useAuditSettingsJurisdictionAdmin'
import CSVFile from '../Atoms/CSVForm'
import { isAuditStarted } from '../AuditAdmin/useRoundsAuditAdmin'
import RoundManagement from './RoundManagement'
import LinkButton from '../Atoms/LinkButton'
import { useBatchInventoryFeatureFlag } from '../useFeatureFlag'
import { StatusBar, AuditHeading } from '../Atoms/StatusBar'
import { assert } from '../utilities'
import { useAuthDataContext } from '../UserContext'
import { Column } from '../Atoms/Layout'
import { candidateTotalsByBatchTemplateCsvPath } from './candidateTotalsByBatchTemplateCsv'

const JurisdictionAdminView: React.FC = () => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const auth = useAuthDataContext()
  const batchInventoryConfig = useBatchInventoryFeatureFlag(jurisdictionId)

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
    !auth?.user ||
    !rounds ||
    !ballotManifest ||
    (isBatchComparison && !batchTallies) ||
    ((isBallotComparison || isHybrid) && !cvrs) ||
    !auditBoards ||
    !auditSettings
  )
    return null // Still loading

  assert(auth.user.type === 'jurisdiction_admin')
  const jurisdiction = auth.user.jurisdictions.find(
    j => j.id === jurisdictionId
  )!

  const isManifestUploaded = isFileProcessed(ballotManifest)
  const isBatchTalliesUploaded =
    !isBatchComparison || isFileProcessed(batchTallies!)
  const isCvrsUploaded =
    !(isBallotComparison || isHybrid) || isFileProcessed(cvrs!)
  const areAllFilesUploaded =
    isManifestUploaded && isBatchTalliesUploaded && isCvrsUploaded

  if (!isAuditStarted(rounds)) {
    return (
      <Wrapper>
        <Inner flexDirection="column">
          <StatusBar>
            <AuditHeading
              auditName={jurisdiction.election.auditName}
              jurisdictionName={jurisdiction.name}
              auditStage="Audit Setup"
            />
          </StatusBar>
          <Column gap="15px">
            {areAllFilesUploaded && (
              <Callout intent="success" icon="tick">
                <strong>Audit setup complete</strong>
                <div>
                  Once your audit administrator starts the audit, check back
                  here to find out which ballots to audit.
                </div>
              </Callout>
            )}
            {isBatchComparison && batchInventoryConfig && (
              <Card elevation={1}>
                <H4>Batch Audit File Preparation Tool</H4>
                <p>
                  Create your{' '}
                  {batchInventoryConfig.showBallotManifest
                    ? 'Ballot Manifest and Candidate Totals by Batch files'
                    : 'Candidate Totals by Batch file'}{' '}
                  using the batch audit file preparation tool.
                </p>
                <p>
                  <LinkButton
                    to={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory`}
                    intent="primary"
                  >
                    Go to Batch Audit File Preparation Tool
                  </LinkButton>
                </p>
              </Card>
            )}
            <Card elevation={1}>
              <CSVFile
                csvFile={ballotManifest}
                uploadCSVFile={uploadBallotManifest}
                deleteCSVFile={deleteBallotManifest}
                title={
                  isHybrid ? 'Ballot Manifest (All ballots)' : 'Ballot Manifest'
                }
                description={
                  isHybrid
                    ? `Click "Browse" to choose the appropriate Ballot
                  Manifest file from your computer. This should be a
                  comma-separated list of all the ballot batches/containers used
                  to store ballots for this particular election, plus a count of
                  how many ballot cards (individual pieces of paper) are stored
                  in each container, and whether each batch has cast vote records.`
                    : `Click "Browse" to choose the appropriate Ballot
                Manifest file from your computer. This should be a
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
            </Card>
            {isBatchComparison && (
              <Card elevation={1}>
                <CSVFile
                  csvFile={batchTallies!}
                  enabled={
                    !!ballotManifest.processing &&
                    ballotManifest.processing.status ===
                      FileProcessingStatus.PROCESSED
                  }
                  uploadCSVFile={uploadBatchTallies}
                  deleteCSVFile={deleteBatchTallies}
                  title="Candidate Totals by Batch"
                  description='Click "Browse" to choose the appropriate Candidate
                  Totals by Batch file from your computer. This should be a
                  comma-separated list of all the ballot boxes/containers used
                  to store ballots for this particular election, plus a count of
                  how many votes were counted for each candidate in each of
                  those containers.'
                  sampleFileLink={candidateTotalsByBatchTemplateCsvPath({
                    electionId,
                    jurisdictionId,
                  })}
                />
              </Card>
            )}
            {(isBallotComparison || isHybrid) && (
              <Card elevation={1}>
                <CSVFile
                  csvFile={cvrs!}
                  enabled={
                    !!ballotManifest.processing &&
                    ballotManifest.processing.status ===
                      FileProcessingStatus.PROCESSED
                  }
                  uploadCSVFile={uploadCVRS}
                  deleteCSVFile={deleteCVRS}
                  title={
                    isHybrid
                      ? 'Cast Vote Records (CVR ballots only)'
                      : 'Cast Vote Records'
                  }
                  description={
                    isHybrid
                      ? `Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file(s) from your computer. This should be an export
                  of all the ballots centrally counted by your tabulator(s),
                  but should not include precinct-count ballots.`
                      : `Click "Browse" to choose the appropriate Cast Vote
                  Records (CVR) file(s) from your computer. This should be an export
                  of all the ballots counted by your tabulator(s).`
                  }
                  showCvrFileType
                />
              </Card>
            )}
          </Column>
        </Inner>
      </Wrapper>
    )
  }
  return (
    <Wrapper>
      <RoundManagement
        round={rounds[rounds.length - 1]}
        auditBoards={auditBoards}
        createAuditBoards={createAuditBoards}
      />
    </Wrapper>
  )
}

export default JurisdictionAdminView

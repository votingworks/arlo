import React from 'react'
import { Card, H4 } from '@blueprintjs/core'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import { StatusBar, AuditHeading } from '../Atoms/StatusBar'
import LinkButton from '../Atoms/LinkButton'
import CSVFile from '../Atoms/CSVForm'
import {
  FileProcessingStatus,
  useBallotManifest,
  useBatchTallies,
  useCVRs,
} from '../useCSV'
import { IJurisdiction } from '../UserContext'
import { useBatchInventoryFeatureFlag } from '../useFeatureFlag'
import useAuditSettingsJurisdictionAdmin from './useAuditSettingsJurisdictionAdmin'
import { Column } from '../Atoms/Layout'

interface IJurisdictionAdminAuditSetupProps {
  jurisdiction: IJurisdiction
}

const JurisdictionAdminAuditSetup: React.FC<IJurisdictionAdminAuditSetupProps> = ({
  jurisdiction,
}) => {
  const { election } = jurisdiction
  const isBatchInventoryEnabled = useBatchInventoryFeatureFlag(jurisdiction.id)
  const auditSettings = useAuditSettingsJurisdictionAdmin(
    election.id,
    jurisdiction.id
  )
  const [
    ballotManifest,
    uploadBallotManifest,
    deleteBallotManifest,
  ] = useBallotManifest(election.id, jurisdiction.id)
  const [
    batchTallies,
    uploadBatchTallies,
    deleteBatchTallies,
  ] = useBatchTallies(
    election.id,
    jurisdiction.id,
    auditSettings,
    ballotManifest
  )
  const [cvrs, uploadCVRS, deleteCVRS] = useCVRs(
    election.id,
    jurisdiction.id,
    auditSettings,
    ballotManifest
  )
  const isBatchComparison =
    auditSettings && auditSettings.auditType === 'BATCH_COMPARISON'
  const isBallotComparison =
    auditSettings && auditSettings.auditType === 'BALLOT_COMPARISON'
  const isHybrid = auditSettings && auditSettings.auditType === 'HYBRID'

  if (
    !ballotManifest ||
    (isBatchComparison && !batchTallies) ||
    ((isBallotComparison || isHybrid) && !cvrs) ||
    !auditSettings
  )
    return null // Still loading

  return (
    <Wrapper>
      <Inner flexDirection="column">
        <StatusBar>
          <AuditHeading
            auditName={election.auditName}
            jurisdictionName={jurisdiction.name}
            auditStage="Audit Setup"
          />
        </StatusBar>
        <Column gap="15px">
          {isBatchComparison && isBatchInventoryEnabled && (
            <Card elevation={1}>
              <H4>Batch Inventory</H4>
              <p>
                Create your Ballot Manifest and Candidate Totals by Batch files
                using the batch inventory worksheet.
              </p>
              <p>
                <LinkButton
                  to={`/election/${election.id}/jurisdiction/${jurisdiction.id}/batch-inventory`}
                  intent="primary"
                >
                  Go to Batch Inventory
                </LinkButton>
              </p>
            </Card>
          )}
          <Card elevation={1}>
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
            </Card>
          )}
        </Column>
      </Inner>
    </Wrapper>
  )
}

export default JurisdictionAdminAuditSetup

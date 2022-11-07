import React from 'react'
import { Card, H4, H3, Callout, Icon } from '@blueprintjs/core'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import { StatusBar, AuditHeading } from '../Atoms/StatusBar'
import LinkButton from '../Atoms/LinkButton'
import CSVFile from '../Atoms/CSVForm'
import { IJurisdiction } from '../UserContext'
import { useBatchInventoryFeatureFlag } from '../useFeatureFlag'
import useAuditSettingsJurisdictionAdmin from './useAuditSettingsJurisdictionAdmin'
import { Column, Row } from '../Atoms/Layout'
import { FileUpload, CvrsFileUpload } from '../Atoms/FileUpload'
import { IAuditSettings } from '../useAuditSettings'
import { useBallotManifest, useBatchTallies, useCVRs } from '../useFileUpload'
import { FileProcessingStatus } from '../useCSV'
import { StepListItem, StepListItemCircle } from '../Atoms/Steps'

const StepCircle: React.FC<{
  stepNumber: number
  state: 'incomplete' | 'complete'
}> = ({ stepNumber, state }) => (
  <StepListItemCircle state="current">
    {state === 'complete' ? <Icon icon="tick" /> : stepNumber}
  </StepListItemCircle>
)

interface IJurisdictionAdminAuditSetupProps {
  jurisdiction: IJurisdiction
  auditSettings: IAuditSettings
}

const JurisdictionAdminAuditSetup: React.FC<IJurisdictionAdminAuditSetupProps> = ({
  jurisdiction,
  auditSettings,
}) => {
  const { election } = jurisdiction
  const { auditType } = auditSettings
  const isBatchInventoryEnabled = useBatchInventoryFeatureFlag(jurisdiction.id)
  const isBallotManifestOnly = auditType === 'BALLOT_POLLING'
  const isCvrsEnabled =
    auditType === 'BALLOT_COMPARISON' || auditType === 'HYBRID'
  const isBatchTalliesEnabled = auditType === 'BATCH_COMPARISON'
  const ballotManifestUpload = useBallotManifest(election.id, jurisdiction.id)
  const batchTalliesUpload = useBatchTallies(election.id, jurisdiction.id, {
    enabled: isBatchTalliesEnabled,
  })
  const cvrsUpload = useCVRs(election.id, jurisdiction.id, {
    enabled: isCvrsEnabled,
  })

  const ballotManifest = ballotManifestUpload.uploadedFile.data
  const isManifestUploaded =
    ballotManifest?.processing?.status === FileProcessingStatus.PROCESSED
  const batchTallies = batchTalliesUpload.uploadedFile.data
  const isBatchTalliesUploaded =
    batchTallies?.processing?.status === FileProcessingStatus.PROCESSED
  const cvrs = cvrsUpload.uploadedFile.data
  const isCvrsUploaded =
    cvrs?.processing?.status === FileProcessingStatus.PROCESSED

  const allFilesUploaded =
    isManifestUploaded &&
    (!isBatchTalliesEnabled || isBatchTalliesUploaded) &&
    (!isCvrsEnabled || isCvrsUploaded)

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
        <Column gap="20px">
          {allFilesUploaded && (
            <Callout intent="success" icon="tick">
              <strong>Audit setup complete!</strong>
              <div>
                Once your audit administrator starts the audit, check back here
                to find out which ballots to audit.
              </div>
            </Callout>
          )}
          {auditType === 'BATCH_COMPARISON' && isBatchInventoryEnabled && (
            <Card elevation={1}>
              <H4>Batch Inventory</H4>
              <p>
                Create your ballot manifest and recorded tallies files using the
                batch inventory worksheet.
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
          <Card elevation={1} style={{ padding: '50px' }}>
            <Row gap="80px" justifyContent="center">
              <Row>
                {!isBallotManifestOnly && (
                  <StepCircle
                    stepNumber={1}
                    state={isManifestUploaded ? 'complete' : 'incomplete'}
                  />
                )}
                <Column
                  style={{ maxWidth: '420px', flex: 1, paddingTop: '2px' }}
                >
                  <H3>Upload your ballot manifest</H3>
                  <p>
                    <Callout
                      style={!isBallotManifestOnly ? { height: '125px' } : {}}
                    >
                      A ballot manifest lists each container of ballots from the
                      election. We&rsquo;ll draw a random sample of ballots to
                      audit based on the manifest.
                    </Callout>
                  </p>
                  <p style={{ marginBottom: '15px' }}>
                    Read more in our{' '}
                    <a
                      href="https://docs.voting.works/arlo/jurisdiction-manager/pre-audit-file-uploads/ballot-manifest"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      instructions for creating a ballot manifest
                    </a>
                    .
                  </p>
                  <FileUpload
                    {...ballotManifestUpload}
                    // title="Ballot Manifest"
                    acceptFileTypes={['csv']}
                  />
                </Column>
              </Row>
              {isBatchTalliesEnabled && (
                <Row>
                  <StepCircle
                    stepNumber={2}
                    state={isBatchTalliesUploaded ? 'complete' : 'incomplete'}
                  />
                  <Column
                    style={{ maxWidth: '420px', flex: 1, paddingTop: '2px' }}
                  >
                    <H3>Upload your recorded tallies</H3>
                    <p>
                      <Callout style={{ height: '125px' }}>
                        The recorded tallies file lists the vote tally for each
                        container of ballots. We&rsquo;ll use the recorded
                        tallies to identify any discrepancies when you audit the
                        sample of ballots.
                      </Callout>
                    </p>
                    <p style={{ marginBottom: '15px' }}>
                      Read more in our{' '}
                      <a
                        href="https://docs.voting.works/arlo/jurisdiction-manager/pre-audit-file-uploads/candidate-totals-by-batch"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        instructions for creating a recorded tallies file
                      </a>
                      .
                    </p>
                    <FileUpload
                      {...batchTalliesUpload}
                      acceptFileTypes={['csv']}
                    />
                  </Column>
                </Row>
              )}
              {isCvrsEnabled && cvrsUpload.uploadedFile.isSuccess && (
                <Row>
                  <StepCircle
                    stepNumber={2}
                    state={isCvrsUploaded ? 'complete' : 'incomplete'}
                  />
                  <Column
                    style={{ maxWidth: '420px', flex: 1, paddingTop: '2px' }}
                  >
                    <H3>Upload your cast vote records</H3>
                    <p>
                      <Callout style={{ height: '125px' }}>
                        Cast vote records (CVRs) list the tabulated votes for
                        each ballot in your voting system. We&rsquo;ll use the
                        cast vote records to identify any discrepancies when you
                        audit the sample of ballots.
                      </Callout>
                    </p>
                    <p style={{ marginBottom: '15px' }}>
                      Read more in our{' '}
                      <a
                        href="https://docs.voting.works/arlo/jurisdiction-manager/pre-audit-file-uploads/cast-vote-records-cvrs"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        instructions for exporting cast vote records
                      </a>
                      .
                    </p>
                    <CvrsFileUpload
                      cvrsUpload={cvrsUpload}
                      uploadDisabled={!isManifestUploaded}
                    />
                  </Column>
                </Row>
              )}
            </Row>
          </Card>
        </Column>
      </Inner>
    </Wrapper>
  )
}

export default JurisdictionAdminAuditSetup

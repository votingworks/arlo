import React from 'react'
import { Card, H4, H3 } from '@blueprintjs/core'
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

  // const allFilesUploaded = isManifestUploaded &&
  // (!isBatchTalliesEnabled || batchTalliesUpload.uploadedFile.data) &&

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
        {auditType === 'BATCH_COMPARISON' && isBatchInventoryEnabled && (
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
        <Card elevation={1} style={{ padding: '100px' }}>
          <Row gap="15px" justifyContent="center">
            <Column style={{ maxWidth: '420px' }}>
              <H3>Upload your ballot manifest</H3>
              <p>
                The ballot manifest lists the tabulated ballots from the
                election. We&rsquo;ll draw a random sample of ballots to audit
                from the manifest.
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
            {isBatchTalliesEnabled && (
              <Card elevation={1}>
                <FileUpload
                  {...batchTalliesUpload}
                  title="Candidate Totals by Batch"
                  acceptFileTypes={['csv']}
                  uploadDisabled={!isManifestUploaded}
                />
              </Card>
            )}
            {isCvrsEnabled && (
              <Card elevation={1}>
                <CvrsFileUpload
                  cvrsUpload={cvrsUpload}
                  uploadDisabled={!isManifestUploaded}
                />
              </Card>
            )}
          </Row>
        </Card>
      </Inner>
    </Wrapper>
  )
}

export default JurisdictionAdminAuditSetup

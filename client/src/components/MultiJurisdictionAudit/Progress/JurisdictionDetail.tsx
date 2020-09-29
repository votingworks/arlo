import React from 'react'
import { Classes, Dialog, H5, H6, Card, Colors } from '@blueprintjs/core'
import styled from 'styled-components'
import {
  IJurisdiction,
  FileProcessingStatus,
  IFileInfo,
} from '../useJurisdictions'
import { JAFileDownloadButtons } from '../RoundManagement'
import { IAuditSettings } from '../../../types'
import { IRound } from '../useRoundsAuditAdmin'
import useAuditBoards from '../useAuditBoards'
import useBallots from '../RoundManagement/useBallots'
import StatusTag from '../../Atoms/StatusTag'

const FileStatusTag = ({
  processing,
}: {
  processing: IFileInfo['processing']
}) => {
  switch (processing && processing.status) {
    case FileProcessingStatus.ERRORED:
      return <StatusTag intent="danger">Upload failed</StatusTag>
    case FileProcessingStatus.PROCESSED:
      return <StatusTag intent="success">Uploaded</StatusTag>
    default:
      return <StatusTag>No file uploaded</StatusTag>
  }
}

const StatusCard = styled(Card)`
  &:not(:last-child) {
    margin-bottom: 20px;
  }
  a.download-link {
    margin-left: 15px;
  }
  p.error {
    margin-top: 10px;
    color: ${Colors.RED3};
  }
`

const FileStatusCard = ({
  title,
  fileInfo,
  downloadUrl,
}: {
  title: string
  fileInfo: IFileInfo
  downloadUrl: string
}) => (
  <StatusCard>
    <H6>{title}</H6>
    <FileStatusTag processing={fileInfo.processing} />
    {fileInfo.file && (
      <a
        className="download-link"
        href={downloadUrl}
        target="_blank"
        rel="noopener noreferrer"
      >
        {fileInfo.file.name}
      </a>
    )}
    {fileInfo.processing && fileInfo.processing.error && (
      <p className="error">{fileInfo.processing.error}</p>
    )}
  </StatusCard>
)

const Section = styled.div`
  &:not(:last-child) {
    padding-bottom: 20px;
  }
`

const JurisdictionDetail = ({
  handleClose,
  jurisdiction,
  electionId,
  round,
  auditSettings,
}: {
  handleClose: () => void
  jurisdiction: IJurisdiction
  electionId: string
  round: IRound | null
  auditSettings: IAuditSettings
}) => (
  <Dialog onClose={handleClose} title={jurisdiction.name} isOpen>
    <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
      <Section>
        <H5>Jurisdiction Files</H5>
        <FileStatusCard
          title="Ballot Manifest"
          fileInfo={jurisdiction.ballotManifest}
          downloadUrl={`/api/election/${electionId}/jurisdiction/${jurisdiction.id}/ballot-manifest/csv`}
        />
        {jurisdiction.batchTallies && (
          <FileStatusCard
            title="Candidate Totals by Batch"
            fileInfo={jurisdiction.batchTallies}
            downloadUrl={`/api/election/${electionId}/jurisdiction/${jurisdiction.id}/batch-tallies/csv`}
          />
        )}
      </Section>
      {round && (
        <RoundStatusSection
          electionId={electionId}
          jurisdiction={jurisdiction}
          round={round}
          auditSettings={auditSettings}
        />
      )}
    </div>
  </Dialog>
)

const RoundStatusSection = ({
  electionId,
  jurisdiction,
  round,
  auditSettings,
}: {
  electionId: string
  jurisdiction: IJurisdiction
  round: IRound
  auditSettings: IAuditSettings
}) => {
  const [auditBoards] = useAuditBoards(electionId, jurisdiction.id, [round])
  const ballots = useBallots(electionId, jurisdiction.id, round.id, auditBoards)
  if (!auditBoards || !ballots) return null
  return (
    <Section>
      <H5>Round {round.roundNum} Data Entry</H5>
      {ballots.length === 0 ? (
        <p>No ballots sampled</p>
      ) : auditBoards.length === 0 ? (
        <p>Waiting for jurisdiction to set up audit boards</p>
      ) : (
        <JAFileDownloadButtons
          electionId={electionId}
          jurisdictionId={jurisdiction.id}
          jurisdictionName={jurisdiction.name}
          round={round}
          auditSettings={auditSettings}
          ballots={ballots}
          auditBoards={auditBoards}
        />
      )}
    </Section>
  )
}

export default JurisdictionDetail

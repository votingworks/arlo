import React from 'react'
import {
  Classes,
  Dialog,
  H5,
  H6,
  Card,
  Colors,
  Button,
} from '@blueprintjs/core'
import styled from 'styled-components'
import { Formik, FormikProps } from 'formik'
import { IJurisdiction, JurisdictionRoundStatus } from '../useJurisdictions'
import { FileProcessingStatus, IFileInfo } from '../useCSV'
import { JAFileDownloadButtons } from '../RoundManagement'
import { IRound } from '../useRoundsAuditAdmin'
import useAuditBoards from '../useAuditBoards'
import StatusTag from '../../Atoms/StatusTag'
import { api } from '../../utilities'
import { IAuditSettings } from '../useAuditSettings'
import useBallotOrBatchCount from '../RoundManagement/useBallots'

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
        {jurisdiction.cvrs && (
          <FileStatusCard
            title="Cast Vote Records (CVR)"
            fileInfo={jurisdiction.cvrs}
            downloadUrl={`/api/election/${electionId}/jurisdiction/${jurisdiction.id}/cvrs/csv`}
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

const unfinalizeResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch/finalize`,
    { method: 'DELETE' }
  ))
}

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
  const numSamples = useBallotOrBatchCount(
    electionId,
    jurisdiction.id,
    round.id,
    auditSettings.auditType
  )
  if (!auditBoards || numSamples === null) return null

  const status = (() => {
    const jurisdictionStatus =
      jurisdiction.currentRoundStatus && jurisdiction.currentRoundStatus.status

    if (round.sampledAllBallots) {
      if (jurisdictionStatus === JurisdictionRoundStatus.COMPLETE)
        return (
          <Formik
            initialValues={{}}
            onSubmit={async () => {
              if (
                await unfinalizeResults(electionId, jurisdiction.id, round.id)
              )
                // Hack: for now just reload the whole page here instead of
                // properly refreshing the state from the server, since the
                // state is way high up in the component hierarchy
                window.location.reload()
            }}
          >
            {({ handleSubmit, isSubmitting }: FormikProps<{}>) => (
              <div>
                <p>Data entry complete and results finalized.</p>
                <Button
                  intent="danger"
                  onClick={handleSubmit as React.FormEventHandler}
                  loading={isSubmitting}
                >
                  Unfinalize Results
                </Button>
              </div>
            )}
          </Formik>
        )
      if (auditBoards.length === 0)
        return <p>Waiting for jurisdiction to set up audit boards</p>
      return (
        <p>Auditing all {jurisdiction.ballotManifest.numBallots} ballots</p>
      )
    }

    const ballotsOrBatches =
      auditSettings.auditType === 'BATCH_COMPARISON' ? 'batches' : 'ballots'

    if (numSamples === 0) return <p>No {ballotsOrBatches} sampled</p>
    if (jurisdictionStatus === JurisdictionRoundStatus.COMPLETE)
      return <p>Data entry complete</p>
    if (auditBoards.length === 0)
      return <p>Waiting for jurisdiction to set up audit boards</p>
    return (
      <JAFileDownloadButtons
        electionId={electionId}
        jurisdictionId={jurisdiction.id}
        jurisdictionName={jurisdiction.name}
        round={round}
        auditSettings={auditSettings}
        auditBoards={auditBoards}
      />
    )
  })()

  return (
    <Section>
      <H5>Round {round.roundNum} Data Entry</H5>
      {status}
    </Section>
  )
}

export default JurisdictionDetail

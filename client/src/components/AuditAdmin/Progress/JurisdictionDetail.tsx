/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import {
  Classes,
  Dialog,
  H5,
  Card,
  Button,
  HTMLSelect,
} from '@blueprintjs/core'
import styled from 'styled-components'
import { Formik, FormikProps } from 'formik'
import { IJurisdiction, JurisdictionRoundStatus } from '../../useJurisdictions'
import { CvrFileType, FileProcessingStatus } from '../../useCSV'
import { IRound } from '../useRoundsAuditAdmin'
import { IAuditSettings } from '../../useAuditSettings'
import { api, assert } from '../../utilities'
import useAuditBoards from '../../useAuditBoards'
import useSampleCount from '../../JurisdictionAdmin/useBallots'
import AsyncButton from '../../Atoms/AsyncButton'
import { JAFileDownloadButtons } from '../../JurisdictionAdmin/RoundManagement'
import FileUpload from '../../Atoms/FileUpload'
import {
  useBallotManifest,
  useBatchTallies,
  useCVRs,
  ICvrsFileUpload,
} from '../../useFileUpload'
import AuditBoardsTable from './AuditBoardsTable'

const StatusCard = styled(Card)`
  &:not(:last-child) {
    margin-bottom: 15px;
  }
`

const Section = styled.div`
  &:not(:last-child) {
    padding-bottom: 20px;
  }
`

export interface IJurisdictionDetailProps {
  handleClose: () => void
  jurisdiction: IJurisdiction
  electionId: string
  round: IRound | null
  auditSettings: IAuditSettings
}

const JurisdictionDetail: React.FC<IJurisdictionDetailProps> = ({
  handleClose,
  jurisdiction,
  electionId,
  round,
  auditSettings,
}) => {
  const cvrsEnabled =
    auditSettings.auditType === 'BALLOT_COMPARISON' ||
    auditSettings.auditType === 'HYBRID'
  const batchTalliesEnabled = auditSettings.auditType === 'BATCH_COMPARISON'
  const ballotManifestUpload = useBallotManifest(electionId, jurisdiction.id)
  const batchTalliesUpload = useBatchTallies(electionId, jurisdiction.id, {
    enabled: batchTalliesEnabled,
  })
  const cvrsUpload = useCVRs(electionId, jurisdiction.id, {
    enabled: cvrsEnabled,
  })

  const ballotManifest = ballotManifestUpload.uploadedFile.data
  const isManifestUploaded =
    ballotManifest &&
    ballotManifest.processing &&
    ballotManifest.processing.status === FileProcessingStatus.PROCESSED

  return (
    <Dialog onClose={handleClose} title={jurisdiction.name} isOpen>
      <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
        <Section>
          <H5>Jurisdiction Files</H5>
          <StatusCard>
            <FileUpload
              title="Ballot Manifest"
              {...ballotManifestUpload}
              acceptFileTypes={['csv']}
              uploadDisabled={round !== null}
              deleteDisabled={round !== null}
            />
          </StatusCard>
          {batchTalliesEnabled && (
            <StatusCard>
              <FileUpload
                title="Candidate Totals by Batch"
                {...batchTalliesUpload}
                acceptFileTypes={['csv']}
                uploadDisabled={!isManifestUploaded || round !== null}
                deleteDisabled={round !== null}
              />
            </StatusCard>
          )}
          {cvrsEnabled && cvrsUpload.uploadedFile.isSuccess && (
            <StatusCard>
              <CvrsFileUpload
                cvrsUpload={cvrsUpload}
                uploadDisabled={!isManifestUploaded || round !== null}
                deleteDisabled={round !== null}
              />
            </StatusCard>
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
}

const CvrsFileUpload = ({
  cvrsUpload,
  uploadDisabled,
  deleteDisabled,
}: {
  cvrsUpload: ICvrsFileUpload
  uploadDisabled?: boolean
  deleteDisabled?: boolean
}) => {
  assert(cvrsUpload.uploadedFile.isSuccess)
  const [selectedCvrFileType, setSelectedCvrFileType] = useState<
    CvrFileType | undefined
  >(cvrsUpload.uploadedFile.data?.file?.cvrFileType)
  const [isUploading, setIsUploading] = useState(false)

  const uploadFiles = async (files: File[]) => {
    setIsUploading(true)
    try {
      await cvrsUpload.uploadFiles(files, selectedCvrFileType!)
    } finally {
      setIsUploading(false)
    }
  }

  const cvrs = cvrsUpload.uploadedFile.data

  return (
    <>
      <FileUpload
        title="Cast Vote Records (CVR)"
        {...cvrsUpload}
        uploadFiles={uploadFiles}
        acceptFileTypes={
          selectedCvrFileType === CvrFileType.HART ? ['zip', 'csv'] : ['csv']
        }
        allowMultipleFiles={
          selectedCvrFileType === CvrFileType.ESS ||
          selectedCvrFileType === CvrFileType.HART
        }
        uploadDisabled={uploadDisabled || (!cvrs.file && !selectedCvrFileType)}
        deleteDisabled={deleteDisabled}
        additionalFields={
          <div>
            <label htmlFor="cvrFileType">CVR File Type: </label>
            <HTMLSelect
              name="cvrFileType"
              id="cvrFileType"
              value={selectedCvrFileType}
              onChange={e =>
                setSelectedCvrFileType(e.target.value as CvrFileType)
              }
              disabled={uploadDisabled || isUploading || cvrs.file !== null}
              style={{ width: '195px', marginLeft: '10px' }}
            >
              <option></option>
              <option value={CvrFileType.DOMINION}>Dominion</option>
              <option value={CvrFileType.CLEARBALLOT}>ClearBallot</option>
              <option value={CvrFileType.ESS}>ES&amp;S</option>
              <option value={CvrFileType.HART}>Hart</option>
            </HTMLSelect>
          </div>
        }
      />
    </>
  )
}

const unfinalizeFullHandTallyResults = async ({
  electionId,
  jurisdictionId,
  roundId,
}: {
  electionId: string
  jurisdictionId: string
  roundId: string
}) => {
  const success = Boolean(
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/finalize`,
      { method: 'DELETE' }
    )
  )
  if (success) {
    // Reload the whole page instead of properly refreshing the state from the server since the
    // state is so high up in the component hierarchy
    // TODO: Use react-query instead
    window.location.reload()
  }
}

const unfinalizeBatchResults = async ({
  electionId,
  jurisdictionId,
  roundId,
}: {
  electionId: string
  jurisdictionId: string
  roundId: string
}) => {
  const success = Boolean(
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/finalize`,
      { method: 'DELETE' }
    )
  )
  if (success) {
    // Reload the whole page instead of properly refreshing the state from the server since the
    // state is so high up in the component hierarchy
    // TODO: Use react-query instead
    window.location.reload()
  }
}

const reopenAuditBoard = async ({
  auditBoardId,
  electionId,
  jurisdictionId,
  roundId,
}: {
  auditBoardId: string
  electionId: string
  jurisdictionId: string
  roundId: string
}) => {
  const success = Boolean(
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board/${auditBoardId}/sign-off`,
      { method: 'DELETE' }
    )
  )
  if (success) {
    // Reload the whole page instead of properly refreshing the state from the server since the
    // state is so high up in the component hierarchy
    // TODO: Use react-query instead
    window.location.reload()
  }
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
  const sampleCount = useSampleCount(
    electionId,
    jurisdiction.id,
    round.id,
    auditSettings.auditType
  )
  if (!auditBoards || !sampleCount) return null

  const status = (() => {
    const jurisdictionStatus =
      jurisdiction.currentRoundStatus && jurisdiction.currentRoundStatus.status
    const auditBoardsTable = (
      <AuditBoardsTable
        auditBoards={auditBoards}
        reopenAuditBoard={auditBoard =>
          reopenAuditBoard({
            auditBoardId: auditBoard.id,
            electionId,
            jurisdictionId: jurisdiction.id,
            roundId: round.id,
          })
        }
      />
    )

    if (round.isFullHandTally) {
      if (jurisdictionStatus === JurisdictionRoundStatus.COMPLETE)
        return (
          <Formik
            initialValues={{}}
            onSubmit={() =>
              unfinalizeFullHandTallyResults({
                electionId,
                jurisdictionId: jurisdiction.id,
                roundId: round.id,
              })
            }
          >
            {({ handleSubmit, isSubmitting }: FormikProps<unknown>) => (
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

    if (sampleCount.ballots === 0) {
      return <p>No ballots sampled</p>
    }
    if (jurisdictionStatus === JurisdictionRoundStatus.COMPLETE) {
      if (auditSettings.auditType === 'BATCH_COMPARISON') {
        return (
          <div>
            <p>Results finalized</p>
            <AsyncButton
              onClick={() =>
                unfinalizeBatchResults({
                  electionId,
                  jurisdictionId: jurisdiction.id,
                  roundId: round.id,
                })
              }
              intent="danger"
            >
              Unfinalize Results
            </AsyncButton>
          </div>
        )
      }
      return (
        <div>
          <p>Data entry complete</p>
          {auditSettings.online && auditBoardsTable}
        </div>
      )
    }
    if (
      auditBoards.length === 0 &&
      auditSettings.auditType !== 'BATCH_COMPARISON'
    ) {
      return <p>Waiting for jurisdiction to set up audit boards</p>
    }
    return (
      <>
        <JAFileDownloadButtons
          electionId={electionId}
          jurisdictionId={jurisdiction.id}
          jurisdictionName={jurisdiction.name}
          round={round}
          auditSettings={auditSettings}
          auditBoards={auditBoards}
        />
        {auditSettings.online && (
          <div style={{ marginTop: '10px' }}>{auditBoardsTable}</div>
        )}
      </>
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

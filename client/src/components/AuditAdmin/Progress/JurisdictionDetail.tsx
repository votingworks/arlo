/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import {
  Classes,
  Dialog,
  H5,
  H6,
  Card,
  Button,
  HTMLSelect,
} from '@blueprintjs/core'
import styled from 'styled-components'
import { Formik, FormikProps } from 'formik'
import { IJurisdiction, JurisdictionRoundStatus } from '../../useJurisdictions'
import { CvrFileType } from '../../useCSV'
import { IRound } from '../useRoundsAuditAdmin'
import { IAuditSettings } from '../../useAuditSettings'
import { api } from '../../utilities'
import useAuditBoards from '../../useAuditBoards'
import useSampleCount from '../../JurisdictionAdmin/useBallots'
import AsyncButton from '../../Atoms/AsyncButton'
import { JAFileDownloadButtons } from '../../JurisdictionAdmin/RoundManagement'
import FileUpload from '../../Atoms/FileUpload'
import {
  useBallotManifest,
  useBatchTallies,
  useCVRs,
} from '../../useFileUpload'

const prettyCvrFileType = (cvrFileType: CvrFileType) =>
  ({
    DOMINION: 'Dominion',
    CLEARBALLOT: 'ClearBallot',
    ESS: 'ES&S',
    HART: 'Hart',
  }[cvrFileType])

const StatusCard = styled(Card)`
  &:not(:last-child) {
    margin-bottom: 20px;
  }
`

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
}) => {
  const ballotManifestUpload = useBallotManifest(electionId, jurisdiction.id)
  const batchTalliesUpload = useBatchTallies(electionId, jurisdiction.id, {
    enabled: !!jurisdiction.batchTallies,
  })
  return (
    <Dialog onClose={handleClose} title={jurisdiction.name} isOpen>
      <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
        <Section>
          <H5>Jurisdiction Files</H5>
          <StatusCard>
            <H6>Ballot Manifest</H6>
            <FileUpload {...ballotManifestUpload} acceptFileType="csv" />
          </StatusCard>
          {jurisdiction.batchTallies && (
            <StatusCard>
              <H6>Candidate Totals by Batch</H6>
              <FileUpload
                {...batchTalliesUpload}
                acceptFileType="csv"
                disabled={
                  ballotManifestUpload.uploadedFile.data &&
                  !ballotManifestUpload.uploadedFile.data.file
                }
              />
            </StatusCard>
          )}
          {jurisdiction.cvrs && (
            <StatusCard>
              <H6>Cast Vote Records (CVR)</H6>
              <CvrsFileUpload
                electionId={electionId}
                jurisdiction={jurisdiction}
                disabled={
                  ballotManifestUpload.uploadedFile.data &&
                  !ballotManifestUpload.uploadedFile.data.file
                }
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
  electionId,
  jurisdiction,
  disabled,
}: {
  electionId: string
  jurisdiction: IJurisdiction
  disabled?: boolean
}) => {
  const cvrsUpload = useCVRs(electionId, jurisdiction.id)
  const [selectedCvrFileType, setSelectedCvrFileType] = useState<CvrFileType>()
  const uploadFiles = (files: FileList) =>
    cvrsUpload.uploadFiles(files, selectedCvrFileType!)

  return (
    <>
      <p>
        <label htmlFor="cvrFileType">CVR File Type: </label>
        {jurisdiction.cvrs!.file ? (
          prettyCvrFileType(jurisdiction.cvrs!.file.cvrFileType!)
        ) : (
          <HTMLSelect
            name="cvrFileType"
            value={selectedCvrFileType}
            onChange={e =>
              setSelectedCvrFileType(e.target.value as CvrFileType)
            }
            disabled={disabled}
          >
            <option></option>
            <option value={CvrFileType.DOMINION}>Dominion</option>
            <option value={CvrFileType.CLEARBALLOT}>ClearBallot</option>
            <option value={CvrFileType.ESS}>ES&amp;S</option>
            <option value={CvrFileType.HART}>Hart</option>
          </HTMLSelect>
        )}
      </p>
      <FileUpload
        {...cvrsUpload}
        uploadFiles={uploadFiles}
        acceptFileType="csv"
        disabled={
          disabled || (!jurisdiction.cvrs!.file && !selectedCvrFileType)
        }
      />
    </>
  )
}

const unfinalizeFullHandTallyResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/finalize`,
    { method: 'DELETE' }
  ))
}

const unfinalizeBatchResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) =>
  !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/finalize`,
    { method: 'DELETE' }
  ))

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

    if (round.isFullHandTally) {
      if (jurisdictionStatus === JurisdictionRoundStatus.COMPLETE)
        return (
          <Formik
            initialValues={{}}
            onSubmit={async () => {
              if (
                await unfinalizeFullHandTallyResults(
                  electionId,
                  jurisdiction.id,
                  round.id
                )
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

    if (sampleCount.ballots === 0) return <p>No ballots sampled</p>
    if (jurisdictionStatus === JurisdictionRoundStatus.COMPLETE)
      if (auditSettings.auditType === 'BATCH_COMPARISON')
        return (
          <div>
            <p>Results finalized</p>
            <AsyncButton
              onClick={async () => {
                if (
                  await unfinalizeBatchResults(
                    electionId,
                    jurisdiction.id,
                    round.id
                  )
                )
                  // Hack: for now just reload the whole page here instead of
                  // properly refreshing the state from the server, since the
                  // state is way high up in the component hierarchy
                  window.location.reload()
              }}
              intent="danger"
            >
              Unfinalize Results
            </AsyncButton>
          </div>
        )
      else return <p>Data entry complete</p>
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

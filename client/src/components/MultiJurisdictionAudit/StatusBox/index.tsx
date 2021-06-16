import React, { ReactElement } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Callout, H3, H4, Button } from '@blueprintjs/core'
import { Formik } from 'formik'
import { IJurisdiction, JurisdictionRoundStatus } from '../useJurisdictions'
import { FileProcessingStatus, IFileInfo } from '../useCSV'
import { apiDownload } from '../../utilities'
import { Inner } from '../../Atoms/Wrapper'
import { IContest } from '../../../types'
import { IAuditBoard } from '../useAuditBoards'
import { IRound, drawSampleError, isAuditStarted } from '../useRoundsAuditAdmin'
import { IAuditSettings } from '../useAuditSettings'

const SpacedH3 = styled(H3)`
  &.bp3-heading {
    margin-bottom: 20px;
  }
`

const Wrapper = styled(Callout)`
  display: flex;
  padding: 30px 0;
  .text {
    flex-grow: 1;
    p {
      margin-bottom: 0;
    }
  }
`

interface IStatusBoxProps {
  headline: string
  details: string[]
  auditName: string
  buttonLabel?: string
  onButtonClick?: () => void
  children?: ReactElement
}

const StatusBox: React.FC<IStatusBoxProps> = ({
  headline,
  details,
  auditName,
  buttonLabel,
  onButtonClick,
  children,
}: IStatusBoxProps) => {
  return (
    <Wrapper icon={null}>
      <Inner>
        <div className="text">
          <SpacedH3>{auditName}</SpacedH3>
          <H4>{headline}</H4>
          {details.map(detail => (
            <p key={detail}>{detail}</p>
          ))}
          {children}
        </div>
        {buttonLabel && onButtonClick && (
          <Formik initialValues={{}} onSubmit={onButtonClick}>
            {({ handleSubmit, isSubmitting }) => (
              <div>
                <Button
                  intent="success"
                  loading={isSubmitting}
                  type="submit"
                  onClick={handleSubmit as React.FormEventHandler}
                >
                  {buttonLabel}
                </Button>
              </div>
            )}
          </Formik>
        )}
      </Inner>
    </Wrapper>
  )
}

const downloadAuditAdminReport = (electionId: string) =>
  apiDownload(`/election/${electionId}/report`)

const downloadJurisdictionAdminReport = (
  electionId: string,
  jurisdictionId: string
) =>
  apiDownload(`/election/${electionId}/jurisdiction/${jurisdictionId}/report`)

export const allCvrsUploaded = (jurisdictions: IJurisdiction[]): boolean =>
  jurisdictions.every(
    ({ cvrs }) =>
      cvrs &&
      cvrs.processing &&
      cvrs.processing.status === FileProcessingStatus.PROCESSED
  )

export const isSetupComplete = (
  jurisdictions: IJurisdiction[],
  contests: IContest[],
  auditSettings: IAuditSettings
): boolean => {
  if (jurisdictions.length === 0) return false

  if (!contests.some(c => c.isTargeted)) return false

  if (Object.values(auditSettings).some(v => v === null)) return false

  const participatingJurisdictions = jurisdictions.filter(({ id }) =>
    contests.some(c => c.jurisdictionIds.includes(id))
  )

  // In batch comparison audits, all jurisdictions must upload batch tallies
  if (auditSettings.auditType === 'BATCH_COMPARISON') {
    if (
      !participatingJurisdictions.every(
        ({ batchTallies }) =>
          batchTallies &&
          batchTallies.processing &&
          batchTallies.processing.status === FileProcessingStatus.PROCESSED
      )
    )
      return false
  }

  // In ballot comparison/hybrid audits, all jurisdictions must upload CVRs
  if (['BALLOT_COMPARISON', 'HYBRID'].includes(auditSettings.auditType)) {
    if (!allCvrsUploaded(participatingJurisdictions)) return false
  }

  return true
}

interface IAuditAdminProps {
  rounds: IRound[]
  startNextRound: () => Promise<boolean>
  undoRoundStart: () => Promise<boolean>
  jurisdictions: IJurisdiction[]
  contests: IContest[]
  auditSettings: IAuditSettings
  children?: ReactElement
}

export const AuditAdminStatusBox: React.FC<IAuditAdminProps> = ({
  rounds,
  startNextRound,
  undoRoundStart,
  jurisdictions,
  contests,
  auditSettings,
  children,
}: IAuditAdminProps) => {
  const { electionId } = useParams<{ electionId: string }>()

  // Audit setup
  if (rounds.length === 0) {
    const details = [
      isSetupComplete(jurisdictions, contests, auditSettings)
        ? 'Audit setup is complete.'
        : 'Audit setup is not complete.',
    ]
    if (jurisdictions.length > 0) {
      const numUploaded = jurisdictions.filter(
        ({ ballotManifest, batchTallies, cvrs }) => {
          const files: IFileInfo['processing'][] = [ballotManifest.processing]
          if (batchTallies) files.push(batchTallies.processing)
          if (cvrs) files.push(cvrs.processing)
          return files.every(
            f => f && f.status === FileProcessingStatus.PROCESSED
          )
        }
      ).length
      details.push(
        `${numUploaded} of ${jurisdictions.length}` +
          ' jurisdictions have completed file uploads.'
      )
    }
    return (
      <StatusBox
        headline="The audit has not started."
        details={details}
        auditName={auditSettings.auditName}
      >
        {children}
      </StatusBox>
    )
  }

  if (drawSampleError(rounds)) {
    return (
      <StatusBox
        headline="Arlo could not draw the sample"
        details={[
          'Please contact our support team for help resolving this issue.',
          `Error: ${drawSampleError(rounds)}`,
        ]}
        auditName={auditSettings.auditName}
        buttonLabel={rounds.length === 1 ? 'Undo Audit Launch' : undefined}
        onButtonClick={rounds.length === 1 ? undoRoundStart : undefined}
      >
        {children}
      </StatusBox>
    )
  }

  const { roundNum, endedAt, isAuditComplete } = rounds[rounds.length - 1]

  // Round in progress
  if (!endedAt) {
    const numCompleted = jurisdictions.filter(
      ({ currentRoundStatus }) =>
        currentRoundStatus!.status === JurisdictionRoundStatus.COMPLETE
    ).length

    const canUndoLaunch =
      roundNum === 1 &&
      jurisdictions.every(
        ({ currentRoundStatus }) =>
          currentRoundStatus!.status !== JurisdictionRoundStatus.IN_PROGRESS
      )

    return (
      <StatusBox
        headline={`Round ${roundNum} of the audit is in progress`}
        details={[
          `${numCompleted} of ${jurisdictions.length} jurisdictions` +
            ` have completed Round ${roundNum}`,
        ]}
        auditName={auditSettings.auditName}
        buttonLabel={canUndoLaunch ? 'Undo Audit Launch' : undefined}
        onButtonClick={canUndoLaunch ? undoRoundStart : undefined}
      >
        {children}
      </StatusBox>
    )
  }

  // Round complete, need another round
  if (!isAuditComplete) {
    return (
      <StatusBox
        headline={`Round ${roundNum} of the audit is complete - another round is needed`}
        details={[`When you are ready, start Round ${roundNum + 1}`]}
        buttonLabel={`Start Round ${roundNum + 1}`}
        onButtonClick={startNextRound}
        auditName={auditSettings.auditName}
      >
        {children}
      </StatusBox>
    )
  }

  // Round complete, audit complete
  return (
    <StatusBox
      headline="Congratulations - the audit is complete!"
      details={[]}
      buttonLabel="Download Audit Report"
      onButtonClick={async () => downloadAuditAdminReport(electionId)}
      auditName={auditSettings.auditName}
    >
      {children}
    </StatusBox>
  )
}

interface IJurisdictionAdminProps {
  rounds: IRound[]
  ballotManifest: IFileInfo
  batchTallies: IFileInfo
  cvrs: IFileInfo
  auditBoards: IAuditBoard[]
  auditType: IAuditSettings['auditType']
  children?: ReactElement
  auditName: string
}

export const JurisdictionAdminStatusBox = ({
  rounds,
  ballotManifest,
  batchTallies,
  cvrs,
  auditBoards,
  auditType,
  children,
  auditName,
}: IJurisdictionAdminProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  // Audit has not started
  if (!isAuditStarted(rounds)) {
    const files: IFileInfo['processing'][] = [ballotManifest.processing]
    if (auditType === 'BATCH_COMPARISON') files.push(batchTallies.processing)
    if (auditType === 'BALLOT_COMPARISON' || auditType === 'HYBRID')
      files.push(cvrs.processing)

    const numComplete = files.filter(
      f => f && f.status === FileProcessingStatus.PROCESSED
    ).length

    let details
    // Special case when we have just a ballotManifest
    if (files.length === 1) {
      details =
        numComplete === 1
          ? [
              'Ballot manifest successfully uploaded.',
              'Waiting for Audit Administrator to launch audit.',
            ]
          : ['Ballot manifest not uploaded.']
    }
    // When we have multiple files
    else {
      details = [`${numComplete}/${files.length} files successfully uploaded.`]
      if (numComplete === files.length)
        details.push('Waiting for Audit Administrator to launch audit.')
    }

    return (
      <StatusBox
        headline="The audit has not started."
        details={details}
        auditName={auditName}
      >
        {children}
      </StatusBox>
    )
  }

  const { roundNum, isAuditComplete, sampledAllBallots } = rounds[
    rounds.length - 1
  ]
  const inProgressHeadline = `Round ${roundNum} of the audit is in progress.`

  // Round in progress, hasn't set up audit boards
  if (auditBoards.length === 0)
    return (
      <StatusBox
        headline={inProgressHeadline}
        details={['Audit boards not set up.']}
        auditName={auditName}
      >
        {children}
      </StatusBox>
    )

  // Round in progress, audit boards set up
  if (!isAuditComplete) {
    if (sampledAllBallots)
      return (
        <StatusBox
          headline={inProgressHeadline}
          details={['Auditing ballots.']}
          auditName={auditName}
        >
          {children}
        </StatusBox>
      )

    const numCompleted = auditBoards.filter(
      ({ currentRoundStatus, signedOffAt }) =>
        currentRoundStatus.numSampledBallots === 0 || signedOffAt
    ).length
    const details = [
      `${numCompleted} of ${auditBoards.length} audit boards complete.`,
    ]
    if (numCompleted === auditBoards.length)
      details.push(
        `Waiting for all jurisdictions to complete Round ${roundNum}.`
      )
    return (
      <StatusBox
        headline={inProgressHeadline}
        details={details}
        auditName={auditName}
      >
        {children}
      </StatusBox>
    )
  }

  // Audit complete
  return (
    <StatusBox
      headline="The audit is complete"
      details={['Download the audit report.']}
      buttonLabel="Download Audit Report"
      onButtonClick={async () =>
        downloadJurisdictionAdminReport(electionId, jurisdictionId)
      }
      auditName={auditName}
    >
      {children}
    </StatusBox>
  )
}

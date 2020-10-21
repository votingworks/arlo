import React, { ReactElement } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import {
  IJurisdiction,
  FileProcessingStatus,
  JurisdictionRoundStatus,
  IFileInfo,
} from '../useJurisdictions'
import FormButton from '../../Atoms/Form/FormButton'
import { api, apiDownload } from '../../utilities'
import { Inner } from '../../Atoms/Wrapper'
import { IAuditSettings, IContest } from '../../../types'
import { IAuditBoard } from '../useAuditBoards'
import { IRound } from '../useRoundsAuditAdmin'

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
  buttonLabel?: string
  onButtonClick?: () => void
  children?: ReactElement
}

const StatusBox: React.FC<IStatusBoxProps> = ({
  headline,
  details,
  buttonLabel,
  onButtonClick,
  children,
}: IStatusBoxProps) => {
  return (
    <Wrapper>
      <Inner>
        <div className="text">
          <H4>{headline}</H4>
          {details.map(detail => (
            <p key={detail}>{detail}</p>
          ))}
          {children}
        </div>
        {buttonLabel && onButtonClick && (
          <FormButton intent="success" onClick={onButtonClick}>
            {buttonLabel}
          </FormButton>
        )}
      </Inner>
    </Wrapper>
  )
}

const createRound = async (electionId: string, roundNum: number) => {
  await api(`/election/${electionId}/round`, {
    method: 'POST',
    body: JSON.stringify({
      roundNum,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

const downloadAuditAdminReport = (electionId: string) => {
  apiDownload(`/election/${electionId}/report`)
}

const downloadJurisdictionAdminReport = (
  electionId: string,
  jurisdictionId: string
) => {
  apiDownload(`/election/${electionId}/jurisdiction/${jurisdictionId}/report`)
}

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

  // In ballot comparison audits, all jurisdictions must upload CVRs
  if (auditSettings.auditType === 'BALLOT_COMPARISON') {
    if (
      !participatingJurisdictions.every(
        ({ cvrs }) =>
          cvrs &&
          cvrs.processing &&
          cvrs.processing.status === FileProcessingStatus.PROCESSED
      )
    )
      return false
  }

  return true
}

interface IAuditAdminProps {
  rounds: IRound[]
  jurisdictions: IJurisdiction[]
  contests: IContest[]
  auditSettings: IAuditSettings
  children?: ReactElement
}

export const AuditAdminStatusBox: React.FC<IAuditAdminProps> = ({
  rounds,
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
      <StatusBox headline="The audit has not started." details={details}>
        {children}
      </StatusBox>
    )
  }

  const { roundNum, endedAt, isAuditComplete } = rounds[rounds.length - 1]

  // Round in progress
  if (!endedAt) {
    const numCompleted = jurisdictions.filter(
      ({ currentRoundStatus }) =>
        currentRoundStatus &&
        currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE
    ).length
    return (
      <StatusBox
        headline={`Round ${roundNum} of the audit is in progress`}
        details={[
          `${numCompleted} of ${jurisdictions.length} jurisdictions` +
            ` have completed Round ${roundNum}`,
        ]}
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
        onButtonClick={() => createRound(electionId, roundNum + 1)}
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
      onButtonClick={() => downloadAuditAdminReport(electionId)}
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
}

export const JurisdictionAdminStatusBox = ({
  rounds,
  ballotManifest,
  batchTallies,
  cvrs,
  auditBoards,
  auditType,
  children,
}: IJurisdictionAdminProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  // Audit has not started
  if (rounds.length === 0) {
    const files: IFileInfo['processing'][] = [ballotManifest.processing]
    if (auditType === 'BATCH_COMPARISON') files.push(batchTallies.processing)
    if (auditType === 'BALLOT_COMPARISON') files.push(cvrs.processing)

    const numComplete = files.filter(
      f => f && f.status === FileProcessingStatus.PROCESSED
    ).length

    let details
    // Special case when we have just a ballotManifest
    if (files.length === 1) {
      details =
        numComplete === 1
          ? [
              'Ballot manifest uploaded.',
              'Waiting for Audit Administrator to launch audit.',
            ]
          : ['Ballot manifest not uploaded.']
    }
    // When we have multiple files
    else {
      details = [`${numComplete}/${files.length} files uploaded.`]
      if (numComplete === files.length)
        details.push('Waiting for Audit Administrator to launch audit.')
    }

    return (
      <StatusBox headline="The audit has not started." details={details}>
        {children}
      </StatusBox>
    )
  }

  const { roundNum, isAuditComplete } = rounds[rounds.length - 1]
  const inProgressHeadline = `Round ${roundNum} of the audit is in progress.`

  // Round in progress, hasn't set up audit boards
  if (auditBoards.length === 0)
    return (
      <StatusBox
        headline={inProgressHeadline}
        details={['Audit boards not set up.']}
      >
        {children}
      </StatusBox>
    )

  // Round in progress, audit boards set up
  if (!isAuditComplete) {
    const numCompleted = auditBoards.filter(
      ({ currentRoundStatus }) =>
        currentRoundStatus.numAuditedBallots ===
        currentRoundStatus.numSampledBallots
    ).length
    const details = [
      `${numCompleted} of ${auditBoards.length} audit boards complete.`,
    ]
    if (numCompleted === auditBoards.length)
      details.push(
        `Waiting for all jurisdictions to complete Round ${roundNum}.`
      )
    return (
      <StatusBox headline={inProgressHeadline} details={details}>
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
      onButtonClick={() =>
        downloadJurisdictionAdminReport(electionId, jurisdictionId)
      }
    >
      {children}
    </StatusBox>
  )
}

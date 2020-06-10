import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import { toast } from 'react-toastify'
import {
  IJurisdiction,
  FileProcessingStatus,
  JurisdictionRoundStatus,
  IFileInfo,
} from '../useJurisdictions'
import FormButton from '../../Atoms/Form/FormButton'
import { api } from '../../utilities'
import { Inner } from '../../Atoms/Wrapper'
import { IAuditSettings, IContest } from '../../../types'
import { IRound } from '../useRoundsJurisdictionAdmin'
import { IAuditBoard } from '../useAuditBoards'

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
}

const StatusBox: React.FC<IStatusBoxProps> = ({
  headline,
  details,
  buttonLabel,
  onButtonClick,
}: IStatusBoxProps) => {
  return (
    <Wrapper>
      <Inner>
        <div className="text">
          <H4>{headline}</H4>
          {details.map(detail => (
            <p key={detail}>{detail}</p>
          ))}
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
  try {
    api(`/election/${electionId}/round`, {
      method: 'POST',
      body: JSON.stringify({
        roundNum,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })
  } catch (err) {
    toast.error(err.message)
  }
}

const downloadAuditAdminReport = (electionId: string) => {
  window.open(`/election/${electionId}/report`)
}

const downloadJurisdictionAdminReport = (
  electionId: string,
  jurisdictionId: string
) => {
  window.open(`/election/${electionId}/jurisdiction/${jurisdictionId}/report`)
}

export const isSetupComplete = (
  jurisdictions: IJurisdiction[],
  contests: IContest[],
  auditSettings: IAuditSettings
): boolean =>
  jurisdictions.length > 0 &&
  contests.some(c => c.isTargeted) &&
  Object.values(auditSettings).every(v => v !== null)

interface IAuditAdminProps {
  rounds: IRound[]
  jurisdictions: IJurisdiction[]
  contests: IContest[]
  auditSettings: IAuditSettings
}

export const AuditAdminStatusBox: React.FC<IAuditAdminProps> = ({
  rounds,
  jurisdictions,
  contests,
  auditSettings,
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
        ({ ballotManifest: { processing } }) =>
          processing && processing.status === FileProcessingStatus.PROCESSED
      ).length
      details.push(
        `${numUploaded} of ${jurisdictions.length}` +
          ' jurisdictions have completed file uploads.'
      )
    }
    return <StatusBox headline="The audit has not started." details={details} />
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
      />
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
      />
    )
  }

  // Round complete, audit complete
  return (
    <StatusBox
      headline="Congratulations - the audit is complete!"
      details={[]}
      buttonLabel="Download Audit Report"
      onButtonClick={() => downloadAuditAdminReport(electionId)}
    />
  )
}

interface IJurisdictionAdminProps {
  rounds: IRound[]
  ballotManifest: IFileInfo
  auditBoards: IAuditBoard[]
}

export const JurisdictionAdminStatusBox = ({
  rounds,
  ballotManifest,
  auditBoards,
}: IJurisdictionAdminProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  // Audit has not started
  if (rounds.length === 0) {
    const { processing } = ballotManifest
    return (
      <StatusBox
        headline="The audit has not started."
        details={
          processing && processing.status === FileProcessingStatus.PROCESSED
            ? [
                'Ballot manifest uploaded.',
                'Waiting for Audit Administrator to launch audit.',
              ]
            : ['Ballot manifest not uploaded.']
        }
      />
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
      />
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
    return <StatusBox headline={inProgressHeadline} details={details} />
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
    />
  )
}

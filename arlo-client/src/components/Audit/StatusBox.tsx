import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import { toast } from 'react-toastify'
import useRoundsAuditAdmin, { IRound } from './useRoundsAuditAdmin'
import useJurisdictions, {
  IJurisdiction,
  FileProcessingStatus,
  JurisdictionRoundStatus,
} from './useJurisdictions'
import FormButton from '../Atoms/Form/FormButton'
import { api } from '../utilities'
import { Inner } from '../Atoms/Wrapper'
import { IAuditSettings, IContest } from '../../types'
import useAuditSettings from './useAuditSettings'
import useContests from './useContests'

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
enum Button {
  START_NEXT_ROUND,
  DOWNLOAD_REPORT,
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

const downloadAuditReport = (electionId: string) => {
  window.open(`/election/${electionId}/audit/report`)
}

export const isSetupComplete = (
  jurisdictions: IJurisdiction[],
  contests: IContest[],
  auditSettings: IAuditSettings
): boolean =>
  jurisdictions.length > 0 &&
  contests.some(c => c.isTargeted) &&
  Object.entries(auditSettings).every(([, v]) => v !== null)

const statusContent = (
  rounds: IRound[],
  jurisdictions: IJurisdiction[],
  contests: IContest[],
  auditSettings: IAuditSettings
): {
  headline: string
  details: string[]
  button: Button | null
} => {
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
    return {
      headline: 'The audit has not started.',
      details,
      button: null,
    }
  }

  const { roundNum, endedAt, isAuditComplete } = rounds[rounds.length - 1]

  // Round in progress
  if (!endedAt) {
    const numCompleted = jurisdictions.filter(
      ({ currentRoundStatus }) =>
        currentRoundStatus &&
        currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE
    ).length
    return {
      headline: `Round ${roundNum} of the audit is in progress`,
      details: [
        `${numCompleted} of ${jurisdictions.length} jurisdictions` +
          ` have completed Round ${roundNum}`,
      ],
      button: Button.START_NEXT_ROUND,
    }
  }

  // Round complete, need another round
  if (!isAuditComplete) {
    return {
      headline: `Round ${roundNum} of the audit is complete - another round is needed`,
      details: [`When you are ready, start Round ${roundNum + 1}`],
      button: Button.DOWNLOAD_REPORT,
    }
  }

  // Round complete, audit complete
  return {
    headline: 'Congratulations - the audit is complete!',
    details: [],
    button: null,
  }
}

const StatusBox: React.FC = () => {
  const { electionId } = useParams<{ electionId: string }>()
  const rounds = useRoundsAuditAdmin(electionId)
  const jurisdictions = useJurisdictions(electionId)
  const [contests] = useContests(electionId)
  const [auditSettings] = useAuditSettings(electionId)

  if (!rounds) return null // Still loading

  const { headline, details, button } = statusContent(
    rounds,
    jurisdictions,
    contests,
    auditSettings
  )

  const buttonElement = (() => {
    switch (button) {
      case Button.START_NEXT_ROUND: {
        const { roundNum } = rounds[rounds.length - 1]
        return (
          <FormButton
            intent="success"
            onClick={() => createRound(electionId, roundNum + 1)}
          >
            Start Round {roundNum + 1}
          </FormButton>
        )
      }
      case Button.DOWNLOAD_REPORT:
        return (
          <FormButton
            intent="success"
            onClick={e => {
              e.preventDefault()
              downloadAuditReport(electionId)
            }}
          >
            Download Audit Report
          </FormButton>
        )
      default:
        return null
    }
  })()

  return (
    <Wrapper>
      <Inner>
        <div className="text">
          <H4>{headline}</H4>
          {details.map(detail => (
            <p key={detail}>{detail}</p>
          ))}
        </div>
        <div>{buttonElement}</div>
      </Inner>
    </Wrapper>
  )
}

export default StatusBox

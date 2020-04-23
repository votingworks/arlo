import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import FormButton from '../../Atoms/Form/FormButton'
import getRound from './getRound'
import getJurisdictions, { IJurisdictionsResponse } from './getJurisdictions'
import { IRound } from '../../../types'

const Wrapper = styled(Callout)`
  .details {
    width: 50%;
  }
  .wrapper {
    margin: 10px 0 10px 0;
    text-align: right;
  }
`

const generateStatuses = (
  totalJurisdictions: number,
  manifestsUploaded: number,
  roundsCompleted: number,
  round: number,
  launched: boolean,
  complete: boolean
): [
  string,
  string[],
  'NO_BUTTON' | 'START_ROUND_BUTTON' | 'DOWNLOAD_BUTTON'
] => {
  if (complete) {
    // all jurisdictions have completed the audit
    return ['The audit is complete.', [], 'DOWNLOAD_BUTTON']
  }
  if (launched && !complete && roundsCompleted === totalJurisdictions) {
    // jurisdictions have finished the round, but another is needed
    return [
      `Round ${round} of the audit is complete - another round needed.`,
      [`When you are ready, start Round ${round + 1}`],
      'START_ROUND_BUTTON',
    ]
  }
  if (launched) {
    // rounds have started
    return [
      `Round ${round} of the audit is in progress.`,
      [
        `${roundsCompleted} of ${totalJurisdictions} have completed Round ${round}`,
      ],
      'NO_BUTTON',
    ]
  }
  // the audit hasn't been launched yet
  return [
    'The audit has not started.',
    [
      'Audit setup is not complete.',
      totalJurisdictions > 0
        ? `${manifestsUploaded} of ${totalJurisdictions} have completed file uploads.`
        : 'No jurisdictions have been created yet.',
    ],
    'NO_BUTTON',
  ]
}

interface IProps {
  electionId: string
  refreshId: string
}

const StatusBox = ({ electionId, refreshId }: IProps) => {
  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
  }

  const [currentRounds, setCurrentRounds] = useState<IRound[]>([])
  const [{ jurisdictions }, setJurisdictions] = useState<
    IJurisdictionsResponse
  >({ jurisdictions: [] })
  useEffect(() => {
    // get pertinent data
    ;(async () => {
      const rounds = await getRound(electionId)
      const jurisdictionList = await getJurisdictions(electionId)
      setCurrentRounds(rounds)
      if (jurisdictionList) setJurisdictions(jurisdictionList)
    })()
  }, [electionId, setCurrentRounds, setJurisdictions, refreshId])

  const [title, details, button] = generateStatuses(
    jurisdictions.length,
    jurisdictions.filter(j => j.ballotManifest.file).length,
    jurisdictions.filter(j => j.currentRoundStatus === currentRounds.length)
      .length,
    currentRounds.length,
    currentRounds.length > 0,
    currentRounds.length > 0 &&
      currentRounds.every(
        r =>
          r.contests.length > 0 &&
          r.contests.every(c => c.endMeasurements.isComplete)
      )
  )

  return (
    <Wrapper>
      <H4>{title}</H4>
      <div className="details">
        {details.map(v => (
          <p key={v}>{v}</p>
        ))}
      </div>
      <div className="wrapper">
        {(() => {
          switch (button) {
            case 'DOWNLOAD_BUTTON':
              return (
                <FormButton intent="success" onClick={downloadAuditReport}>
                  Download Audit Reports
                </FormButton>
              )
            case 'START_ROUND_BUTTON': // button to submit to the rounds endpoint with a new round number
            case 'NO_BUTTON':
            default:
              return null
          }
        })()}
      </div>
    </Wrapper>
  )
}

export default StatusBox

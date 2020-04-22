import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import FormButton from '../../Atoms/Form/FormButton'
import getRound from './getRound'
import getJurisdictions, { IJurisdictionsResponse } from './getJurisdictions'

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
  if (!complete && roundsCompleted === totalJurisdictions) {
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
      `${manifestsUploaded} of ${totalJurisdictions} have completed file uploads.`,
    ],
    'NO_BUTTON',
  ]
}

interface IProps {
  electionId: string
}

const StatusBox = ({ electionId }: IProps) => {
  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
  }

  const [currentRound, setCurrentRound] = useState(0)
  const [{ jurisdictions }, setJurisdictions] = useState<
    IJurisdictionsResponse
  >({ jurisdictions: [] })
  useEffect(() => {
    // get pertinent data
    ;(async () => {
      const round = await getRound(electionId)
      const jurisdictionList = await getJurisdictions(electionId)
      setCurrentRound(round)
      if (jurisdictionList) setJurisdictions(jurisdictionList)
    })()
  }, [electionId, setCurrentRound, setJurisdictions])
  console.log(jurisdictions)

  const [title, details, button] = generateStatuses(
    jurisdictions.length,
    jurisdictions.filter(j => j.ballotManifest.file).length,
    jurisdictions.filter(j => j.currentRoundStatus === currentRound).length,
    currentRound,
    currentRound > 0,
    false
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

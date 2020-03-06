import React from 'react'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import { IAudit } from '../../types'
import FormButton from '../Form/FormButton'

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
  audit: IAudit,
  launched: boolean,
  started: boolean,
  complete: boolean
): [string, string | undefined] => {
  if (complete) {
    // all jurisdictions have completed the audit
    return ['The audit is complete.', undefined]
  }
  if (launched && started) {
    // rounds have started
    return [
      `Round ${audit.rounds.length} of the audit is in progress.`,
      undefined,
    ]
  }
  if (launched && !started) {
    // after setup before first round
    return ['The audit has not started.', 'Audit setup is complete.']
  }
  /* istanbul ignore next */
  return ['The audit has not launched.', 'Audit setup is not complete.']
}

interface IProps {
  audit: IAudit
  electionId: string
  launched: boolean
  started: boolean
}

const StatusBox = ({ audit, electionId, launched, started }: IProps) => {
  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
  }

  const complete = audit.rounds.length
    ? audit.rounds[audit.rounds.length - 1].contests.every(
        c => c.endMeasurements.isComplete
      )
    : false

  const [auditStatus, setupStatus] = generateStatuses(
    audit,
    launched,
    started,
    complete
  )

  return (
    <Wrapper>
      <H4>{auditStatus}</H4>
      <div className="details">{setupStatus && <p>{setupStatus}</p>}</div>
      <div className="wrapper">
        <FormButton
          disabled={!complete}
          intent={complete ? 'success' : 'none'}
          onClick={downloadAuditReport}
        >
          Download Audit Reports {!complete && '(Incomplete)'}
        </FormButton>
      </div>
    </Wrapper>
  )
}

export default StatusBox

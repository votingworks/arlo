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
  const STATUSES = {
    audit: [
      'The audit has not launched.',
      'The audit has not started.',
      `Round ${audit.rounds.length} of the audit is in progress.`,
      'The audit is complete.',
    ],
    setup: [
      'Audit setup is not complete.',
      'Audit setup is complete.',
      undefined,
    ],
  }

  if (complete) {
    // all jurisdictions have completed the audit
    return [STATUSES.audit[3], STATUSES.setup[2]]
  } else if (launched && started) {
    // rounds have started
    return [STATUSES.audit[2], STATUSES.setup[2]]
  } else if (launched && !started) {
    // after setup before first round
    return [STATUSES.audit[1], STATUSES.setup[1]]
  }
  /* istanbul ignore next */
  return [STATUSES.audit[0], STATUSES.setup[0]]
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

import React from 'react'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import { IAudit } from '../../types'
import FormButton from '../Form/FormButton'

const Wrapper = styled(Callout)`
  .details {
    width: 50%;
  }
  .bp3-button {
    float: right;
  }
`

const generateStatuses = (audit: IAudit) => {
  const manifestsUploaded = audit.jurisdictions.filter(
    j => j.ballotManifest && j.ballotManifest.filename
  ).length
  const completedJurisdictions = 0 // This will need to be derived from the /ballot-list endpoint using each jurisdictionID
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
    jurisdictions: [
      undefined,
      `${manifestsUploaded} of ${audit.jurisdictions.length} jurisdictions have completed file uploads.`,
      `${completedJurisdictions} of ${audit.jurisdictions.length} jurisdictions have completed Round ${audit.rounds.length}.`,
    ],
  }

  if (!audit.launched) {
    // during setup before launch
    return [STATUSES.audit[0], STATUSES.setup[0], STATUSES.jurisdictions[0]]
  } else if (audit.launched && !audit.started) {
    // after setup before first round
    return [STATUSES.audit[1], STATUSES.setup[1], STATUSES.jurisdictions[1]]
  } else if (audit.launched && audit.started) {
    // rounds have started
    return [STATUSES.audit[2], STATUSES.setup[2], STATUSES.jurisdictions[2]]
  } else if (audit.complete) {
    // all jurisdictions have completed the audit
    return [STATUSES.audit[3], STATUSES.setup[2], STATUSES.jurisdictions[2]]
  }
  return [STATUSES.audit[0], STATUSES.setup[0], STATUSES.jurisdictions[0]]
}

interface IProps {
  audit: IAudit
  electionId: string
}

const StatusBox = ({ audit, electionId }: IProps) => {
  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
  }

  const [auditStatus, setupStatus, jurisdictionStatus] = generateStatuses(audit)

  return (
    <Wrapper>
      <H4>{auditStatus}</H4>
      <div className="details">
        {setupStatus && <p>{setupStatus}</p>}
        {jurisdictionStatus && <p>{jurisdictionStatus}</p>}
      </div>
      <FormButton disabled={!audit.complete} onClick={downloadAuditReport}>
        Download Audit Reports {!audit.complete && '(Incomplete)'}
      </FormButton>
    </Wrapper>
  )
}

export default StatusBox

import React from 'react'
import styled from 'styled-components'
import { Callout, H4 } from '@blueprintjs/core'
import { IStatus, IAudit } from '../../types'
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
      'The audit has not started.',
      `Round ${audit.rounds.length} of the audit is in progress.`,
      'The audit is complete.',
    ],
    setup: ['Audit setup is not complete.', 'Audit setup is complete.'],
    jurisdictions: [
      `${manifestsUploaded} of ${audit.jurisdictions.length} jurisdictions have completed file uploads.`,
      `${completedJurisdictions} of ${audit.jurisdictions.length} jurisdictions have completed Round ${audit.rounds.length}.`,
    ],
  }

  if (!audit.name) {
    return [STATUSES.audit[0], STATUSES.setup[0], STATUSES.jurisdictions[0]]
  }
  return [STATUSES.audit[0], STATUSES.setup[0], STATUSES.jurisdictions[0]]
}

interface IProps {
  audit: IAudit
  status: IStatus
  electionId: string
}

const StatusBox = ({ audit, status, electionId }: IProps) => {
  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
  }

  const [auditStatus, setupStatus, jurisdictionStatus] = generateStatuses(audit)

  return (
    <Wrapper>
      <H4>{auditStatus}</H4>
      <div className="details">
        <p>{setupStatus}</p>
        <p>{jurisdictionStatus}</p>
      </div>
      <FormButton disabled={!status.isComplete} onClick={downloadAuditReport}>
        Download Audit Reports {!status.isComplete && '(Incomplete)'}
      </FormButton>
    </Wrapper>
  )
}

export default StatusBox

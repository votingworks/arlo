import React, { useState } from 'react'
import styled from 'styled-components'
import { H1 } from '@blueprintjs/core'

import ElectionResultsCard from './ElectionResultsCard'
import { IElectionResultsFormState } from './electionResults'
import { Inner } from '../../Atoms/Wrapper'

const PageHeading = styled(H1)`
  margin-bottom: 24px;
  text-align: center;
`

const AuditPlanner: React.FC = () => {
  const [electionResultsEditable, setElectionResultsEditable] = useState(true)

  const planAudit = (_electionResults: IElectionResultsFormState) => {
    setElectionResultsEditable(false)
  }

  const enableEditing = () => {
    setElectionResultsEditable(true)
  }

  return (
    <Inner flexDirection="column" withTopPadding>
      <PageHeading>Audit Planner</PageHeading>
      <ElectionResultsCard
        editable={electionResultsEditable}
        enableEditing={enableEditing}
        planAudit={planAudit}
      />
    </Inner>
  )
}

export default AuditPlanner

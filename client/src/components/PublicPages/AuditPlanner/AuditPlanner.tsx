import React, { useState } from 'react'
import styled from 'styled-components'
import { H1 } from '@blueprintjs/core'

import AuditPlanCard from './AuditPlanCard'
import ElectionResultsCard from './ElectionResultsCard'
import {
  assertIsElectionResults,
  IElectionResults,
  IElectionResultsFormState,
} from './electionResults'
import { Inner } from '../../Atoms/Wrapper'

const PageHeading = styled(H1)`
  margin-bottom: 24px;
  text-align: center;
`

const AuditPlanner: React.FC = () => {
  const [savedElectionResults, setSavedElectionResults] = useState<
    IElectionResults
  >()
  const [areElectionResultsEditable, setAreElectionResultsEditable] = useState(
    true
  )

  const planAudit = (electionResultsFormState: IElectionResultsFormState) => {
    assertIsElectionResults(electionResultsFormState)
    setSavedElectionResults(electionResultsFormState)
    setAreElectionResultsEditable(false)
  }

  const enableElectionResultsEditing = () => {
    setAreElectionResultsEditable(true)
  }

  const clearElectionResults = () => {
    setSavedElectionResults(undefined)
    setAreElectionResultsEditable(true)
  }

  return (
    <Inner flexDirection="column" withTopPadding>
      <PageHeading>Audit Planner</PageHeading>
      <ElectionResultsCard
        clearElectionResults={clearElectionResults}
        editable={areElectionResultsEditable}
        enableElectionResultsEditing={enableElectionResultsEditing}
        planAudit={planAudit}
      />
      {savedElectionResults && (
        <AuditPlanCard
          disabled={areElectionResultsEditable}
          electionResults={savedElectionResults}
        />
      )}
    </Inner>
  )
}

export default AuditPlanner

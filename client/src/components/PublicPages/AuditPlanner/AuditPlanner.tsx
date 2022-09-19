import React, { useState } from 'react'
import styled from 'styled-components'
import { Colors, H1 } from '@blueprintjs/core'

import AuditPlanCard from './AuditPlanCard'
import ElectionResultsCard from './ElectionResultsCard'
import {
  assertIsElectionResults,
  IElectionResults,
  IElectionResultsFormState,
} from './electionResults'
import { Inner } from '../../Atoms/Wrapper'

const Container = styled(Inner)`
  // Undo the override in App.css and restore to Blueprint's original heading color
  .bp3-heading {
    color: ${Colors.DARK_GRAY1};
  }
`

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
  }

  return (
    <Container flexDirection="column" withTopPadding>
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
    </Container>
  )
}

export default AuditPlanner

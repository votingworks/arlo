import React from 'react'
import styled from 'styled-components'
import { Card, H2, Callout } from '@blueprintjs/core'
import { Inner } from '../Atoms/Wrapper'
import BatchRoundTallyEntry from '../JurisdictionAdmin/BatchRoundSteps/BatchRoundTallyEntry'
import { useBatches } from '../JurisdictionAdmin/useBatchResults'

const Heading = styled(H2)`
  margin-bottom: 16px;
`

const BatchRoundTallyEntryContainer = styled(Card)`
  margin-top: 10px;
  overflow-x: scroll;
  padding: 0;
`

interface ITallyEntryScreenProps {
  electionId: string
  jurisdictionId: string
  roundId: string
}

const TallyEntryScreen: React.FC<ITallyEntryScreenProps> = ({
  electionId,
  jurisdictionId,
  roundId,
}) => {
  const batchesQuery = useBatches(electionId, jurisdictionId, roundId)

  if (!batchesQuery.isSuccess) {
    return null
  }

  const { resultsFinalizedAt } = batchesQuery.data

  return (
    <Inner flexDirection="column" withTopPadding>
      <Heading>Enter Tallies</Heading>
      {resultsFinalizedAt && (
        <Callout intent="success">
          <strong>Tallies finalized</strong>
        </Callout>
      )}
      <BatchRoundTallyEntryContainer>
        <BatchRoundTallyEntry
          electionId={electionId}
          jurisdictionId={jurisdictionId}
          roundId={roundId}
        />
      </BatchRoundTallyEntryContainer>
    </Inner>
  )
}

export default TallyEntryScreen

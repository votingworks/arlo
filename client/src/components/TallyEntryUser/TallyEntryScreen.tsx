import React from 'react'
import styled from 'styled-components'
import { Card, H2 } from '@blueprintjs/core'
import { Inner } from '../Atoms/Wrapper'
import BatchRoundTallyEntry from '../JurisdictionAdmin/BatchRoundSteps/BatchRoundTallyEntry'

const Heading = styled(H2)`
  margin-bottom: 16px;
`

const BatchRoundTallyEntryContainer = styled(Card)`
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
  return (
    <Inner flexDirection="column" withTopPadding>
      <Heading>Enter Tallies</Heading>
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

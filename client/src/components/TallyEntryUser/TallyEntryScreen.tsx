import React from 'react'
import { H2 } from '@blueprintjs/core'
import { Inner } from '../Atoms/Wrapper'
import BatchRoundTallyEntry from '../JurisdictionAdmin/BatchRoundSteps/BatchRoundTallyEntry'

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
      <H2>Enter Tallies</H2>
      <BatchRoundTallyEntry
        electionId={electionId}
        jurisdictionId={jurisdictionId}
        roundId={roundId}
      />
    </Inner>
  )
}

export default TallyEntryScreen

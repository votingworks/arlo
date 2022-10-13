import React from 'react'
import { H2 } from '@blueprintjs/core'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import BatchRoundDataEntry from '../JurisdictionAdmin/BatchRoundDataEntry'

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
      <BatchRoundDataEntry
        electionId={electionId}
        jurisdictionId={jurisdictionId}
        roundId={roundId}
        showFinalizeAndCopyButtons={false}
      />
    </Inner>
  )
}

export default TallyEntryScreen

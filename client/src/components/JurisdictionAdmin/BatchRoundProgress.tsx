import React from 'react'
import { ProgressBar, Classes } from '@blueprintjs/core'
import styled from 'styled-components'
import { useBatches } from './useBatchResults'
import { Row } from '../Atoms/Layout'

interface IBatchRoundProgressProps {
  electionId: string
  jurisdictionId: string
  roundId: string
}

const BatchRoundProgressContainer = styled(Row).attrs({
  gap: '15px',
  alignItems: 'center',
})`
  > * {
    flex-shrink: 0;
  }
  .${Classes.PROGRESS_BAR} {
    width: 150px;
  }
`

const BatchRoundProgress: React.FC<IBatchRoundProgressProps> = ({
  electionId,
  jurisdictionId,
  roundId,
}) => {
  const batchesQuery = useBatches(electionId, jurisdictionId, roundId)

  if (!batchesQuery.isSuccess) return null // Still loading
  const { batches } = batchesQuery.data
  const numAudited = batches.filter(batch => batch.resultTallySheets.length > 0)
    .length

  return (
    <BatchRoundProgressContainer>
      <div>
        <strong>
          {numAudited}/{batches.length} batches audited
        </strong>
      </div>
      <ProgressBar
        value={numAudited / batches.length}
        stripes={false}
        intent="primary"
      />
    </BatchRoundProgressContainer>
  )
}

export default BatchRoundProgress

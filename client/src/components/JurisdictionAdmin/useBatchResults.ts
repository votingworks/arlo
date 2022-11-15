import { useQuery, useMutation, useQueryClient } from 'react-query'
import { fetchApi } from '../../utils/api'

export interface IBatchResults {
  [choiceId: string]: number
}

export interface IBatchResultTallySheet {
  name: string
  results: IBatchResults
}

export interface IBatch {
  id: string
  lastEditedBy: string | null
  name: string
  numBallots: number
  resultTallySheets: IBatchResultTallySheet[]
}

export interface IBatches {
  batches: IBatch[]
  resultsFinalizedAt: string | null
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useBatches = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) =>
  useQuery<IBatches>('batches', () =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches`
    )
  )

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useRecordBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const putBatchResults = async ({
    batchId,
    resultTallySheets,
  }: {
    batchId: string
    resultTallySheets: IBatchResultTallySheet[]
  }) =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/${batchId}/results`,
      {
        method: 'PUT',
        body: JSON.stringify(resultTallySheets),
        headers: { 'Content-Type': 'application/json' },
      }
    )

  const queryClient = useQueryClient()

  return useMutation(putBatchResults, {
    onSuccess: () => queryClient.invalidateQueries('batches'),
  })
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useFinalizeBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const finalizeBatchResults = async () =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/finalize`,
      { method: 'POST' }
    )

  const queryClient = useQueryClient()

  return useMutation(finalizeBatchResults, {
    onSuccess: () => queryClient.invalidateQueries('batches'),
  })
}

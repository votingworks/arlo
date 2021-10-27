import { useQuery, useMutation, useQueryClient } from 'react-query'
import { fetchApi } from '../../SupportTools/support-api'

export interface IBatchResults {
  [choiceId: string]: number
}

export interface IBatch {
  id: string
  name: string
  numBallots: number
  auditBoard: null | {
    id: string
    name: string
  }
  results: IBatchResults | null
}

interface IBatches {
  batches: IBatch[]
  resultsFinalizedAt: string
}

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

export const useRecordBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const putBatchResults = async ({
    batchId,
    results,
  }: {
    batchId: string
    results: IBatchResults
  }) =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/${batchId}/results`,
      {
        method: 'PUT',
        body: JSON.stringify(results),
        headers: { 'Content-Type': 'application/json' },
      }
    )

  const queryClient = useQueryClient()

  return useMutation(putBatchResults, {
    onSuccess: () => queryClient.invalidateQueries('batches'),
  })
}

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

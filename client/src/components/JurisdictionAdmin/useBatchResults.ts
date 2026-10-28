import {
  useQuery,
  useMutation,
  useQueryClient,
  UseMutationResult,
  UseQueryResult,
} from 'react-query'
import { ApiError, fetchApi } from '../../utils/api'

export interface IBatchResults {
  [choiceId: string]: number
}

export interface IBatchResultTallySheet {
  name: string
  results: IBatchResults
}

export interface IBatch {
  contestIdsToAudit: string[]
  id: string
  lastEditedBy: string | null
  name: string
  numBallots: number
  resultTallySheets: IBatchResultTallySheet[]
}

export interface IBatches {
  batches: IBatch[]
  resultsFinalizedAt: string | null
  roundNum: number
}

export const useBatches = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): UseQueryResult<IBatches, ApiError> =>
  useQuery<IBatches, ApiError>('batches', () =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches`
    )
  )

interface IRecordBatchResultsArgs {
  batchId: string
  resultTallySheets: IBatchResultTallySheet[]
}

export const useRecordBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): UseMutationResult<unknown, ApiError, IRecordBatchResultsArgs> => {
  const putBatchResults = async ({
    batchId,
    resultTallySheets,
  }: IRecordBatchResultsArgs) =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/${batchId}/results`,
      {
        method: 'PUT',
        body: JSON.stringify(resultTallySheets),
        headers: { 'Content-Type': 'application/json' },
      }
    )

  const queryClient = useQueryClient()

  return useMutation<unknown, ApiError, IRecordBatchResultsArgs>(
    putBatchResults,
    {
      onSuccess: () => queryClient.invalidateQueries('batches'),
    }
  )
}

export const useFinalizeBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): UseMutationResult<unknown, ApiError, void> => {
  const finalizeBatchResults = async () =>
    fetchApi(
      `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/finalize`,
      { method: 'POST' }
    )

  const queryClient = useQueryClient()

  return useMutation<unknown, ApiError, void>(finalizeBatchResults, {
    onSuccess: () => queryClient.invalidateQueries('batches'),
  })
}

import {
  UseQueryResult,
  useQuery,
  UseMutationResult,
  useMutation,
  useQueryClient,
} from 'react-query'
import { IContest } from '../types'
import { IAuditSettings } from './useAuditSettings'
import { ApiError, fetchApi } from '../utils/api'

export const contestsQueryKey = (electionId: string): string[] => [
  'elections',
  electionId,
  'contests',
]

export const useContests = (
  electionId: string
): UseQueryResult<IContest[], ApiError> =>
  useQuery(contestsQueryKey(electionId), async () => {
    const response = await fetchApi(`/api/election/${electionId}/contest`)
    return response.contests
  })

export const useUpdateContests = (
  electionId: string,
  auditType: IAuditSettings['auditType']
): UseMutationResult<IContest[], ApiError, IContest[]> => {
  const putContests = (newContests: IContest[]) =>
    fetchApi(`/api/election/${electionId}/contest`, {
      method: 'PUT',
      body: JSON.stringify(
        newContests
          // Remove totalBallotsCast unless this is a ballot polling audit
          .map(({ totalBallotsCast, ...c }) =>
            auditType === 'BALLOT_POLLING' ? { totalBallotsCast, ...c } : c
          )
          // Remove pendingBallots unless this is a batch comparison audit
          .map(({ pendingBallots, ...c }) =>
            auditType === 'BATCH_COMPARISON' ? { pendingBallots, ...c } : c
          )
      ),
      headers: { 'Content-Type': 'application/json' },
    })

  const queryClient = useQueryClient()

  return useMutation(putContests, {
    onSuccess: () => {
      queryClient.invalidateQueries(contestsQueryKey(electionId))
    },
  })
}

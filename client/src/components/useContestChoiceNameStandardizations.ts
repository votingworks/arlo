import {
  useMutation,
  UseMutationResult,
  useQuery,
  useQueryClient,
  UseQueryResult,
} from 'react-query'

import { ApiError, fetchApi } from '../utils/api'
import { contestsQueryKey } from './useContests'

export interface IContestChoiceNameStandardizations {
  [jurisdictionId: string]: {
    [contestId: string]: {
      [cvrChoiceName: string]: string | null // Standardized choice name
    }
  }
}

export interface IContestChoiceNameStandardizationsResponse {
  standardizations: IContestChoiceNameStandardizations
}

export const contestChoiceNameStandardizationsQueryKey = (
  electionId: string
): string[] => ['election', electionId, 'contestChoiceNameStandardizations']

export const useContestChoiceNameStandardizations = (
  electionId: string
): UseQueryResult<IContestChoiceNameStandardizationsResponse, ApiError> =>
  useQuery<IContestChoiceNameStandardizationsResponse, ApiError>(
    contestChoiceNameStandardizationsQueryKey(electionId),
    () => {
      return fetchApi(
        `/api/election/${electionId}/contest/choice-name-standardizations`
      )
    }
  )

export const useUpdateContestChoiceNameStandardizations = (
  electionId: string
): UseMutationResult<
  IContestChoiceNameStandardizations,
  ApiError,
  IContestChoiceNameStandardizations
> => {
  const queryClient = useQueryClient()

  const putStandardizations = (
    newStandardizations: IContestChoiceNameStandardizations
  ) => {
    return fetchApi(
      `/api/election/${electionId}/contest/choice-name-standardizations`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newStandardizations),
      }
    )
  }

  return useMutation(putStandardizations, {
    onSuccess: () => {
      queryClient.invalidateQueries(
        contestChoiceNameStandardizationsQueryKey(electionId)
      )
      queryClient.invalidateQueries(contestsQueryKey(electionId))
    },
  })
}

import {
  UseQueryOptions,
  UseQueryResult,
  useQuery,
  UseMutationResult,
  useQueryClient,
  useMutation,
} from 'react-query'
import { FileProcessingStatus } from '../useCSV'
import { ISampleSizeOption } from './Setup/Review/useSampleSizes'
import { fetchApi, ApiError } from '../../utils/api'

export interface IRound {
  id: string
  roundNum: number
  startedAt: string
  endedAt: string | null
  isAuditComplete: boolean
  needsFullHandTally: boolean
  isFullHandTally: boolean
  drawSampleTask: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  }
}

export interface ISampleSizes {
  [contestId: string]: ISampleSizeOption
}

export const isDrawingSample = (rounds: IRound[]): boolean =>
  rounds.length > 0 &&
  rounds[rounds.length - 1].drawSampleTask.completedAt === null

export const isDrawSampleComplete = (rounds: IRound[]): boolean =>
  rounds.length > 0 &&
  rounds[rounds.length - 1].drawSampleTask.completedAt !== null

export const drawSampleError = (rounds: IRound[]): string | null =>
  rounds.length > 0 ? rounds[rounds.length - 1].drawSampleTask.error : null

export const isAuditStarted = (rounds: IRound[]): boolean =>
  rounds.length > 0 && isDrawSampleComplete(rounds) && !drawSampleError(rounds)

export const roundsQueryKey = (electionId: string): string[] => [
  'elections',
  electionId,
  'rounds',
]

export const useRounds = (
  electionId: string,
  options?: UseQueryOptions<IRound[], ApiError, IRound[], string[]>
): UseQueryResult<IRound[], ApiError> =>
  useQuery(
    roundsQueryKey(electionId),
    async () => {
      const response: { rounds: IRound[] } = await fetchApi(
        `/api/election/${electionId}/round`
      )
      return response.rounds
    },
    options
  )

interface ICreateRoundBody {
  roundNum: number
  sampleSizes: ISampleSizes
}

export const useStartNextRound = (
  electionId: string
): UseMutationResult<unknown, ApiError, ICreateRoundBody> => {
  const postRound = async (body: ICreateRoundBody) =>
    fetchApi(`/api/election/${electionId}/round`, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: {
        'Content-Type': 'application/json',
      },
    })

  const queryClient = useQueryClient()

  return useMutation(postRound, {
    onSuccess: () => {
      queryClient.invalidateQueries(roundsQueryKey(electionId))
    },
  })
}

export const useFinishRound = (
  electionId: string
): UseMutationResult<unknown, ApiError, void> => {
  const postFinishRound = async () =>
    fetchApi(`/api/election/${electionId}/round/current/finish`, {
      method: 'POST',
    })

  const queryClient = useQueryClient()

  return useMutation(postFinishRound, {
    onSuccess: () => {
      queryClient.invalidateQueries(roundsQueryKey(electionId))
    },
  })
}

export const useUndoRoundStart = (
  electionId: string
): UseMutationResult<unknown, ApiError, string> => {
  const deleteRound = async (roundId: string) =>
    fetchApi(`/api/election/${electionId}/round/${roundId}`, {
      method: 'DELETE',
    })

  const queryClient = useQueryClient()

  return useMutation(deleteRound, {
    onSuccess: () => {
      queryClient.invalidateQueries(roundsQueryKey(electionId))
    },
  })
}

const samplePreviewQueryKey = (electionId: string): string[] => [
  'elections',
  electionId,
  'sample-preview',
]

export const useComputeSamplePreview = (
  electionId: string
): UseMutationResult<unknown, ApiError, ISampleSizes> => {
  const postSamplePreview = async (sampleSizes: ISampleSizes) =>
    fetchApi(`/api/election/${electionId}/sample-preview`, {
      method: 'POST',
      body: JSON.stringify({ sampleSizes }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

  const queryClient = useQueryClient()
  return useMutation(postSamplePreview, {
    onSuccess: () => {
      queryClient.invalidateQueries(samplePreviewQueryKey(electionId))
    },
  })
}

interface ISamplePreviewJurisdiction {
  name: string
  numSamples: number
  numUnique: number
}

export interface ISamplePreview {
  jurisdictions: ISamplePreviewJurisdiction[] | null
  task: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  }
}

export const useSamplePreview = (
  electionId: string,
  options: UseQueryOptions<ISamplePreview, ApiError> = {}
): UseQueryResult<ISamplePreview, ApiError> =>
  useQuery<ISamplePreview, ApiError>(
    samplePreviewQueryKey(electionId),
    async () => fetchApi(`/api/election/${electionId}/sample-preview`),
    options
  )

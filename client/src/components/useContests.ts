import { useEffect, useState } from 'react'
import uuidv4 from 'uuidv4'
import {
  UseQueryResult,
  useQuery,
  UseMutationResult,
  useMutation,
  useQueryClient,
} from 'react-query'
import { api } from './utilities'
import { IContest } from '../types'
import { parse as parseNumber } from '../utils/number-schema'
import { IAuditSettings } from './useAuditSettings'
import { ApiError, fetchApi } from '../utils/api'

export interface IContestNumbered {
  id: string
  isTargeted: boolean
  name: string
  numWinners: number
  votesAllowed: number
  choices: {
    id: string
    name: string
    numVotes: number
  }[]
  totalBallotsCast: number
  jurisdictionIds: string[]
}

export const numberifyContest = (contest: IContest): IContestNumbered => {
  return {
    id: contest.id || uuidv4(), // preserve given id if present, generate new one if empty string
    name: contest.name,
    isTargeted: contest.isTargeted,
    totalBallotsCast: parseNumber(contest.totalBallotsCast),
    numWinners: parseNumber(contest.numWinners),
    votesAllowed: parseNumber(contest.votesAllowed),
    jurisdictionIds: contest.jurisdictionIds,
    choices: contest.choices.map(choice => ({
      id: choice.id || uuidv4(),
      name: choice.name,
      numVotes: parseNumber(choice.numVotes),
    })),
  }
}

const contestsQueryKey = (electionId: string) => [
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
      // stringify and numberify the contests (all number values are handled as strings clientside, but are required as numbers serverside)
      body: JSON.stringify(
        newContests
          .map(c => numberifyContest(c))
          // Remove totalBallotsCast unless this is a ballot polling audit
          .map(({ totalBallotsCast, ...c }) =>
            auditType === 'BALLOT_POLLING' ? { totalBallotsCast, ...c } : c
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

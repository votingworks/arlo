import { useEffect, useState } from 'react'
import uuidv4 from 'uuidv4'
import { api } from '../utilities'
import { IContest } from '../../types'
import { parse as parseNumber } from '../../utils/number-schema'
import { IAuditSettings } from './useAuditSettings'

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

const getContests = async (electionId: string): Promise<IContest[] | null> => {
  const response = await api<{ contests: IContest[] }>(
    `/election/${electionId}/contest`
  )
  if (!response) return null
  return response.contests
}

const useContests = (
  electionId: string,
  auditType?: IAuditSettings['auditType'],
  refreshId?: string
): [IContest[] | null, (arg0: IContest[]) => Promise<boolean>] => {
  const [contests, setContests] = useState<IContest[] | null>(null)

  const updateContests = async (newContests: IContest[]): Promise<boolean> => {
    if (!contests) return false
    const response = await api(`/election/${electionId}/contest`, {
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
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response) return false
    setContests(await getContests(electionId))
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newContests = await getContests(electionId)
      setContests(newContests)
    })()
  }, [electionId, refreshId])
  return [contests, updateContests]
}

export default useContests

import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import uuidv4 from 'uuidv4'
import { api } from '../utilities'
import { IContest } from '../../types'
import { parse as parseNumber } from '../../utils/number-schema'

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

const useContests = (
  electionId: string
): [IContest[], (arg0: IContest[]) => Promise<boolean>] => {
  const [contests, setContests] = useState<IContest[]>([])

  const getContests = async (): Promise<IContest[]> => {
    try {
      const response: { contests: IContest[] } = await api(
        `/election/${electionId}/contest`
      )
      return response.contests
    } catch (err) {
      toast.error(err.message)
      return contests
    }
  }

  const updateContests = async (newContests: IContest[]): Promise<boolean> => {
    const oldContests = await getContests()
    const updatedContests: IContest[] = oldContests.reduce(
      (a: IContest[], c) => {
        const matchingContest = newContests.findIndex(v => v.id === c.id)
        // replace old contest with new contest that has the same id, then remove it from newContests
        if (matchingContest > -1) {
          a.push(newContests[matchingContest])
          newContests.splice(matchingContest, 1)
        } else {
          a.push(c)
        }
        return a
      },
      []
    )
    const mergedContests = [
      ...updatedContests,
      // merge in all the new contests that weren't found by id
      ...newContests,
    ]
    try {
      await api(`/election/${electionId}/contest`, {
        method: 'PUT',
        // stringify and numberify the contests (all number values are handled as strings clientside, but are required as numbers serverside)
        body: JSON.stringify({
          contests: mergedContests.map(c => numberifyContest(c)),
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    } catch (err) {
      toast.error(err.message)
      return false
    }
    setContests(mergedContests)
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newContests = await getContests()
      setContests(newContests)
    })()
  }, [getContests])
  return [contests, updateContests]
}

export default useContests

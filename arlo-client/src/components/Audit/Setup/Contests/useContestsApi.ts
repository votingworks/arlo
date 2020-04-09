import { useEffect, useCallback, useState, useMemo } from 'react'
import uuidv4 from 'uuidv4'
import { api, checkAndToast } from '../../../utilities'
import { IErrorResponse, IContest } from '../../../../types'
import { IContests } from './types'
import { parse as parseNumber } from '../../../../utils/number-schema'

interface IContestNumbered {
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

const numberifyContest = (contest: IContest): IContestNumbered => {
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

const useContestsApi = (
  electionId: string,
  isTargeted: boolean
): [IContests, (arg0: IContest[]) => Promise<boolean>] => {
  const defaultValues: IContests = useMemo(
    () => ({
      contests: [
        {
          id: '',
          name: '',
          isTargeted,
          totalBallotsCast: '',
          numWinners: '1',
          votesAllowed: '1',
          jurisdictionIds: [],
          choices: [
            {
              id: '',
              name: '',
              numVotes: '',
            },
            {
              id: '',
              name: '',
              numVotes: '',
            },
          ],
        },
      ],
    }),
    [isTargeted]
  )
  const [contests, setContests] = useState(defaultValues)

  const getContests = useCallback(async (): Promise<IContests> => {
    const contestsOrError: IContests | IErrorResponse = await api(
      `/election/${electionId}/contest`
    )
    if (checkAndToast(contestsOrError)) {
      return defaultValues
    }
    return contestsOrError
  }, [electionId, defaultValues])

  const updateContests = async (newContests: IContest[]): Promise<boolean> => {
    const oldContests = await getContests()
    const updatedContests: IContest[] = oldContests.contests.reduce(
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
    const mergedContests = {
      contests: [
        ...updatedContests,
        // merge in all the new contests that weren't found by id
        ...newContests,
      ],
    }
    const response: IErrorResponse = await api(
      `/election/${electionId}/contest`,
      {
        method: 'PUT',
        // stringify and numberify the contests (all number values are handled as strings clientside, but are required as numbers serverside)
        body: JSON.stringify(
          mergedContests.contests.map(c => numberifyContest(c))
        ),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    if (checkAndToast(response)) {
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

export default useContestsApi

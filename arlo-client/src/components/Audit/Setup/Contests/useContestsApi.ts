import { useEffect, useCallback, useState } from 'react'
import uuidv4 from 'uuidv4'
import { api, checkAndToast } from '../../../utilities'
import { IErrorResponse, IContest } from '../../../../types'
import { IContests } from './types'

const useContestsApi = (
  electionId: string,
  isTargeted: boolean
): [IContests, (arg0: IContest[]) => Promise<boolean>] => {
  const defaultValues: IContests = {
    contests: [
      {
        id: '',
        name: '',
        isTargeted,
        totalBallotsCast: '',
        numWinners: '1',
        votesAllowed: '1',
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
  }
  const [contests, setSettings] = useState(defaultValues)

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
        // merge in all the new contests that weren't found by id, and generate unique ids for them
        ...newContests.map(c => ({ ...c, id: uuidv4() })),
      ],
    }
    const response: IErrorResponse = await api(
      `/election/${electionId}/contest`,
      {
        method: 'PUT',
        body: JSON.stringify(mergedContests),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    if (checkAndToast(response)) {
      return false
    }
    setSettings(mergedContests)
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newContests = await getContests()
      setSettings(newContests)
    })()
  }, [getContests])
  return [contests, updateContests]
}

export default useContestsApi

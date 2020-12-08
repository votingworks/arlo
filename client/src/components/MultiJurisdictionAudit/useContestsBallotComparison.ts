import { useEffect, useState } from 'react'
import { api } from '../utilities'

export interface IContest {
  id: string
  name: string
  isTargeted: boolean
  numWinners: number
  jurisdictionIds: string[]
}

const getContests = async (electionId: string): Promise<IContest[] | null> => {
  const response = await api<{ contests: IContest[] }>(
    `/election/${electionId}/contest`
  )
  return response && response.contests
}

const putContests = async (
  electionId: string,
  newContests: IContest[]
): Promise<boolean> =>
  !!api(`/election/${electionId}/contest`, {
    method: 'PUT',
    body: JSON.stringify(newContests),
    headers: { 'Content-Type': 'application/json' },
  })

const useContestsBallotComparison = (
  electionId: string
): [IContest[] | null, (newContests: IContest[]) => Promise<boolean>] => {
  const [contests, setContests] = useState<IContest[] | null>(null)

  const updateContests = async (newContests: IContest[]) => {
    if (putContests(electionId, newContests)) {
      setContests(await getContests(electionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      setContests(await getContests(electionId))
    })()
  }, [electionId])

  return [contests, updateContests]
}

export default useContestsBallotComparison

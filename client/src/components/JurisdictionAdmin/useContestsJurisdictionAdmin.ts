import { useEffect, useState } from 'react'
import { api } from '../utilities'
import { IContest } from '../../types'

const getContests = async (
  electionId: string,
  jurisdictionId: string
): Promise<IContest[] | null> => {
  const response = await api<{ contests: IContest[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/contest`
  )
  if (!response) return null
  return response.contests
}

const useContestsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
): IContest[] | null => {
  const [contests, setContests] = useState<IContest[] | null>(null)

  useEffect(() => {
    ;(async () => {
      const newContests = await getContests(electionId, jurisdictionId)
      setContests(newContests)
    })()
  }, [electionId, jurisdictionId])
  return contests
}

export default useContestsJurisdictionAdmin

import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../utilities'
import { IContest } from '../../../types'

const getContests = async (
  electionId: string,
  jurisdictionId: string
): Promise<IContest[] | null> => {
  try {
    const response: { contests: IContest[] } = await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/contest`
    )
    return response.contests
  } catch (err) {
    toast.error(err.message)
    return null
  }
}

const useContests = (
  electionId: string,
  jurisdictionId: string
): IContest[] | null => {
  const [contests, setContests] = useState<IContest[] | null>(null)

  useEffect(() => {
    ;(async () => {
      const newContests = await getContests(electionId, jurisdictionId)
      setContests(newContests)
    })()
  }, [electionId])
  return contests
}

export default useContests

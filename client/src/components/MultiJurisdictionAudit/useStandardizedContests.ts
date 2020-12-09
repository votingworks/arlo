import { useEffect, useState } from 'react'
import { api } from '../utilities'

export interface IStandardizedContest {
  name: string
  jurisdictionIds: string[]
}

const getStandardizedContests = async (
  electionId: string
): Promise<IStandardizedContest[] | null> =>
  api(`/election/${electionId}/standardized-contests`)

const useStandardizedContests = (
  electionId: string
): IStandardizedContest[] | null => {
  const [standardizedContests, setStandardizedContests] = useState<
    IStandardizedContest[] | null
  >(null)

  useEffect(() => {
    ;(async () => {
      setStandardizedContests(await getStandardizedContests(electionId))
    })()
  }, [electionId])

  return standardizedContests
}

export default useStandardizedContests

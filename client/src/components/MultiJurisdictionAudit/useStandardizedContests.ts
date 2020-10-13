import { useEffect, useState } from 'react'
import uuidv4 from 'uuidv4'
import { api } from '../utilities'

export interface IStandardizedContest {
  id: string
  name: string
  jurisdictionIds: string[]
}

const uuidify = ({
  id,
  name,
  jurisdictionIds,
}: IStandardizedContest): IStandardizedContest => ({
  id: id || uuidv4(),
  name,
  jurisdictionIds,
})

const getStandardizedContests = async (
  electionId: string
): Promise<IStandardizedContest[] | null> => {
  const response = await api<IStandardizedContest[]>(
    `/election/${electionId}/standardized-contests`
  )
  if (!response) return null
  return response.map(c => uuidify(c))
}

const useStandardizedContests = (
  electionId: string,
  refreshId?: string
): [
  IStandardizedContest[] | null,
  (arg0: IStandardizedContest[]) => Promise<boolean>
] => {
  const [standardizedContests, setContests] = useState<
    IStandardizedContest[] | null
  >(null)

  const updateStandardizedContests = async (
    newContests: IStandardizedContest[]
  ): Promise<boolean> => {
    const response = await api(`/election/${electionId}/contest`, {
      method: 'PUT',
      // stringify and numberify the contests (all number values are handled as strings clientside, but are required as numbers serverside)
      body: JSON.stringify(newContests),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response) return false
    setContests(newContests)
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newContests = await getStandardizedContests(electionId)
      setContests(newContests)
    })()
  }, [electionId, refreshId])
  return [standardizedContests, updateStandardizedContests]
}

export default useStandardizedContests

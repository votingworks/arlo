import { useEffect, useState } from 'react'
import { api } from '../utilities'

const dummyStandardizedContests: IStandardizedContest[] = [
  {
    name: 'Contest One',
    jurisdictionIds: ['one', 'two'],
  },
  {
    name: 'Contest Two',
    jurisdictionIds: [],
  },
  {
    name: 'Contest Three',
    jurisdictionIds: ['one', 'three', 'four'],
  },
]

export interface IStandardizedContest {
  name: string
  jurisdictionIds: string[]
}

// adding in dummy data until backend works
const getStandardizedContests = async (
  electionId: string
): Promise<IStandardizedContest[] | null> => {
  const response = await api<IStandardizedContest[]>(
    `/election/${electionId}/standardized-contests`
  )
  return response
    ? [...response, ...dummyStandardizedContests]
    : dummyStandardizedContests
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

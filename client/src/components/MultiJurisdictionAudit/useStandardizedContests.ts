import { useEffect, useState } from 'react'
import uuidv4 from 'uuidv4'
import { api, areArraysEqualSets } from '../utilities'
import { IContest } from '../../types'

export interface IStandardizedContest {
  name: string
  jurisdictionIds: string[]
}

export interface IStandardizedContestOption extends IStandardizedContest {
  id: string
  checked: boolean
}

export interface ISelectedStandardizedContest
  extends IStandardizedContestOption {
  isTargeted: boolean
}

type ISubmitContest = Pick<
  ISelectedStandardizedContest,
  'id' | 'name' | 'isTargeted' | 'jurisdictionIds'
>

const getStandardizedContests = async (
  electionId: string
): Promise<IStandardizedContest[] | null> =>
  api<IStandardizedContest[]>(`/election/${electionId}/standardized-contests`)

const getContests = async (electionId: string): Promise<IContest[] | null> => {
  const response = await api<{ contests: IContest[] }>(
    `/election/${electionId}/contest`
  )
  if (!response) return null
  return response.contests
}

const useStandardizedContests = (
  electionId: string,
  refreshId?: string
): [
  IStandardizedContestOption[] | null,
  (arg0: ISelectedStandardizedContest[]) => Promise<boolean>
] => {
  const [standardizedContests, setStandardizedContests] = useState<
    IStandardizedContestOption[] | null
  >(null)
  const [contests, setContests] = useState<IContest[] | null>(null)

  const updateContests = async (
    newContests: ISelectedStandardizedContest[]
  ): Promise<boolean> => {
    if (!standardizedContests || !contests) return false

    const newStandardizedContests: IStandardizedContestOption[] = []
    const mergedContests: ISubmitContest[] = newContests.reduce(
      (
        a: ISubmitContest[],
        {
          id,
          name,
          isTargeted,
          jurisdictionIds,
          checked,
        }: ISelectedStandardizedContest
      ) => {
        newStandardizedContests.push({ id, name, jurisdictionIds, checked })
        const matchedContest = contests.find(c => c.id === id)
        if (matchedContest && !checked) return a
        return [...a, { id, name, isTargeted, jurisdictionIds }]
      },
      []
    )

    const response = await api(`/election/${electionId}/contest`, {
      method: 'PUT',
      body: JSON.stringify(mergedContests),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response) return false
    setStandardizedContests(newStandardizedContests)
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newContests = await getContests(electionId)
      const newStandardizedContests = await getStandardizedContests(electionId)
      if (!newContests || !newStandardizedContests) return
      setStandardizedContests(
        newStandardizedContests.map(sc => {
          const selectedContest = newContests.find(
            c =>
              c.name === sc.name &&
              areArraysEqualSets(c.jurisdictionIds, sc.jurisdictionIds)
          )
          return {
            ...sc,
            id: selectedContest ? selectedContest.id : uuidv4(),
            checked: !!selectedContest,
          }
        })
      )
      setContests(newContests)
    })()
  }, [electionId, refreshId])
  return [standardizedContests, updateContests]
}

export default useStandardizedContests

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
  isTargeted: boolean
}

type ISubmitContest = Pick<
  IStandardizedContestOption,
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
  targetedView: boolean,
  refreshId?: string
): [
  IStandardizedContestOption[] | null,
  (arg0: IStandardizedContestOption[]) => Promise<boolean>
] => {
  const [standardizedContests, setStandardizedContests] = useState<
    IStandardizedContestOption[] | null
  >(null)
  const [contests, setContests] = useState<IContest[] | null>(null)

  const updateContests = async (
    newContests: IStandardizedContestOption[]
  ): Promise<boolean> => {
    if (!standardizedContests || !contests) return false

    const mergedContests: ISubmitContest[] = newContests.reduce(
      (
        a: ISubmitContest[],
        {
          id,
          name,
          isTargeted,
          jurisdictionIds,
          checked,
        }: IStandardizedContestOption
      ) => {
        if (isTargeted !== targetedView || checked)
          return [...a, { id, name, isTargeted, jurisdictionIds }]
        return a
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
    setStandardizedContests(newContests)
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
            isTargeted: selectedContest
              ? selectedContest.isTargeted
              : targetedView,
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

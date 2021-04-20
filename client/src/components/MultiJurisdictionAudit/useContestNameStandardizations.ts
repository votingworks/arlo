import { useEffect, useState } from 'react'
import { api } from '../utilities'

export interface IContestNameStandardizations {
  standardizations: {
    [jurisdictionId: string]: {
      [contestName: string]: string | null // CVR contest name
    }
  }
  cvrContestNames: {
    [jurisdictionId: string]: string[]
  }
}

const getStandardizations = async (electionId: string) =>
  api<IContestNameStandardizations>(
    `/election/${electionId}/contest/standardizations`
  )

const useContestNameStandardizations = (
  electionId: string
): [
  IContestNameStandardizations | null,
  (
    standardizations: IContestNameStandardizations['standardizations']
  ) => Promise<boolean>
] => {
  const [
    standardizations,
    setStandardizations,
  ] = useState<IContestNameStandardizations | null>(null)

  const updateStandardizations = async (
    newStandardizations: IContestNameStandardizations['standardizations']
  ): Promise<boolean> => {
    const response = await api(
      `/election/${electionId}/contest/standardizations`,
      {
        method: 'PUT',
        body: JSON.stringify(newStandardizations),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    if (response) setStandardizations(await getStandardizations(electionId))
    return !!response
  }

  useEffect(() => {
    ;(async () => {
      setStandardizations(await getStandardizations(electionId))
    })()
  }, [electionId])

  return [standardizations, updateStandardizations]
}

export default useContestNameStandardizations

import { useEffect, useState } from 'react'
import { useQueryClient } from 'react-query'
import { api } from './utilities'
import { IAuditSettings } from './useAuditSettings'
import { contestsQueryKey } from './useContests'
import { contestChoiceNameStandardizationsQueryKey } from './useContestChoiceNameStandardizations'

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
  electionId: string,
  auditSettings: IAuditSettings | null
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
  const queryClient = useQueryClient()

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
    if (response) {
      setStandardizations(await getStandardizations(electionId))
    }
    await queryClient.invalidateQueries(
      contestChoiceNameStandardizationsQueryKey(electionId)
    )
    await queryClient.invalidateQueries(contestsQueryKey(electionId))
    return !!response
  }

  const auditType = auditSettings && auditSettings.auditType

  useEffect(() => {
    ;(async () => {
      if (auditType === null) return
      if (auditType === 'BALLOT_COMPARISON' || auditType === 'HYBRID')
        setStandardizations(await getStandardizations(electionId))
      // Set to empty values for other audit types so the consuming code knows
      // we're not still trying to load (signified by null)
      else setStandardizations({ standardizations: {}, cvrContestNames: {} })
    })()
  }, [electionId, auditType])

  return [standardizations, updateStandardizations]
}

export default useContestNameStandardizations

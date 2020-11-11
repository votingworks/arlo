import { useEffect, useState } from 'react'
import { api } from '../../utilities'

export interface IOfflineBatchResults {
  finalizedAt: string
  results: {
    batchName: string
    choiceResults: {
      [choiceId: string]: number
    }
  }[]
}

const getResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IOfflineBatchResults | null> => {
  return api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch`
  )
}

const putResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  newResults: IOfflineBatchResults['results']
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch`,
    {
      method: 'PUT',
      body: JSON.stringify(newResults),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  ))
}

const postFinalizeResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch/finalize`,
    {
      method: 'POST',
    }
  ))
}

const useOfflineBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): [
  IOfflineBatchResults | null,
  (newResults: IOfflineBatchResults['results']) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [results, setResults] = useState<IOfflineBatchResults | null>(null)

  const updateResults = async (
    newResults: IOfflineBatchResults['results']
  ): Promise<boolean> => {
    const success = await putResults(
      electionId,
      jurisdictionId,
      roundId,
      newResults
    )
    if (success)
      setResults(await getResults(electionId, jurisdictionId, roundId))
    return success
  }

  const finalizeResults = async (): Promise<boolean> => {
    const success = await postFinalizeResults(
      electionId,
      jurisdictionId,
      roundId
    )
    if (success) {
      setResults(await getResults(electionId, jurisdictionId, roundId))
    }
    return success
  }

  useEffect(() => {
    ;(async () => {
      const loadedResults = await getResults(
        electionId,
        jurisdictionId,
        roundId
      )
      if (loadedResults) setResults(loadedResults)
    })()
  }, [electionId, jurisdictionId, roundId])
  return [results, updateResults, finalizeResults]
}

export default useOfflineBatchResults

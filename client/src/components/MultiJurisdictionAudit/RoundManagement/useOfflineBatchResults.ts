import { useEffect, useState } from 'react'
import { api } from '../../utilities'

export interface IOfflineBatchResult {
  batchName: string
  batchType:
    | 'Absentee By Mail'
    | 'Advance'
    | 'Election Day'
    | 'Provisional'
    | 'Other'
    | ''
  choiceResults: {
    [choiceId: string]: number | string
  }
}

export interface IOfflineBatchResults {
  finalizedAt: string
  results: IOfflineBatchResult[]
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

const postResult = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  newResult: IOfflineBatchResult
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch/`,
    {
      method: 'POST',
      body: JSON.stringify(newResult),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  ))
}

const putResult = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  batchName: string,
  newResult: IOfflineBatchResult
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch/${encodeURIComponent(
      batchName
    )}`,
    {
      method: 'PUT',
      body: JSON.stringify(newResult),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  ))
}

const deleteResult = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  batchName: string
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results/batch/${encodeURIComponent(
      batchName
    )}`,
    {
      method: 'DELETE',
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
  (newResult: IOfflineBatchResult) => Promise<boolean>,
  (batchName: string, newResult: IOfflineBatchResult) => Promise<boolean>,
  (batchName: string) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [results, setResults] = useState<IOfflineBatchResults | null>(null)

  const addResult = async (
    newResult: IOfflineBatchResult
  ): Promise<boolean> => {
    const success = await postResult(
      electionId,
      jurisdictionId,
      roundId,
      newResult
    )
    if (success)
      setResults(await getResults(electionId, jurisdictionId, roundId))
    return success
  }

  const updateResult = async (
    batchName: string,
    newResult: IOfflineBatchResult
  ): Promise<boolean> => {
    const success = await putResult(
      electionId,
      jurisdictionId,
      roundId,
      batchName,
      newResult
    )
    if (success)
      setResults(await getResults(electionId, jurisdictionId, roundId))
    return success
  }

  const removeResult = async (batchName: string): Promise<boolean> => {
    const success = await deleteResult(
      electionId,
      jurisdictionId,
      roundId,
      batchName
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

  return [results, addResult, updateResult, removeResult, finalizeResults]
}

export default useOfflineBatchResults

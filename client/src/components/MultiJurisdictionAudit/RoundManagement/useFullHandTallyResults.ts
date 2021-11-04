import { useEffect, useState } from 'react'
import { api } from '../../utilities'

export interface IFullHandTallyBatchResult {
  batchName: string
  batchType:
    | 'Absentee By Mail'
    | 'Advance'
    | 'Election Day'
    | 'Provisional'
    | 'Other'
    | ''
  choiceResults: {
    [choiceId: string]: number
  }
}

export interface IFullHandTallyBatchResults {
  finalizedAt: string
  results: IFullHandTallyBatchResult[]
}

const getResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IFullHandTallyBatchResults | null> => {
  return api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/batch`
  )
}

const postResult = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  newResult: IFullHandTallyBatchResult
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/batch/`,
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
  newResult: IFullHandTallyBatchResult
): Promise<boolean> => {
  return !!(await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/batch/${encodeURIComponent(
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
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/batch/${encodeURIComponent(
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
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/full-hand-tally/finalize`,
    {
      method: 'POST',
    }
  ))
}

const useFullHandTallyResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): [
  IFullHandTallyBatchResults | null,
  (newResult: IFullHandTallyBatchResult) => Promise<boolean>,
  (batchName: string, newResult: IFullHandTallyBatchResult) => Promise<boolean>,
  (batchName: string) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [results, setResults] = useState<IFullHandTallyBatchResults | null>(
    null
  )

  const addResult = async (
    newResult: IFullHandTallyBatchResult
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
    newResult: IFullHandTallyBatchResult
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

export default useFullHandTallyResults

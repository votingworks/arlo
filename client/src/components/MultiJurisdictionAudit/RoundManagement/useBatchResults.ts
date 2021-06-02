import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../utilities'

export interface IResultValues {
  [batchId: string]: {
    [choiceId: string]: number | string
  }
}

export interface IBatch {
  id: string
  name: string
  numBallots: number
  auditBoard: null | {
    id: string
    name: string
  }
}

const stringifyPossibleNull = (v: string | number | null) => (v ? `${v}` : '')

const reformatResults = (r: IResultValues, numberify = true): IResultValues => {
  return Object.keys(r).reduce(
    (a, batchId) => ({
      ...a,
      [batchId]: Object.keys(r[batchId]).reduce(
        (b, choiceId) => ({
          ...b,
          [choiceId]: numberify
            ? Number(r[batchId][choiceId])
            : stringifyPossibleNull(r[batchId][choiceId]),
        }),
        {}
      ),
    }),
    {}
  )
}

const numberifyResults = (r: IResultValues): IResultValues => reformatResults(r)

const getResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IResultValues | null> => {
  const response = await api<IResultValues>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/results`
  )
  if (!response) return null
  return reformatResults(response, false)
}

export const getBatches = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IBatch[] | null> => {
  const response = await api<{ batches: IBatch[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches`
  )
  if (!response) return null
  return response.batches
}

const useBatchResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): [
  IResultValues | null,
  IBatch[] | null,
  (arg0: IResultValues) => Promise<boolean>
] => {
  const [results, setResults] = useState<IResultValues | null>(null)
  const [batches, setBatches] = useState<IBatch[] | null>(null)

  const updateResults = async (newResults: IResultValues): Promise<boolean> => {
    try {
      await api(
        `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/results`,
        {
          method: 'PUT',
          // stringify and numberify the contests (all number values are handled as strings clientside, but are required as numbers serverside)
          body: JSON.stringify(numberifyResults(newResults)),
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
    } catch (err) /* istanbul ignore next */ {
      // TODO move toasting into api
      toast.error(err.message)
      return false
    }
    setResults(newResults)
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newBatches = await getBatches(electionId, jurisdictionId, roundId)
      const newResults = await getResults(electionId, jurisdictionId, roundId)
      setBatches(newBatches)
      setResults(newResults)
    })()
  }, [electionId, jurisdictionId, roundId])
  return [results, batches, updateResults]
}

export default useBatchResults

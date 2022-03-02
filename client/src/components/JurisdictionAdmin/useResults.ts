import { useEffect, useState } from 'react'
import { api } from '../utilities'

export interface IResultValues {
  [contestId: string]: {
    [choiceId: string]: number | string
  }
}

const stringifyPossibleNull = (v: string | number | null) => (v ? `${v}` : '')

const reformatResults = (r: IResultValues, numberify = true): IResultValues => {
  return Object.keys(r).reduce(
    (a, contestId) => ({
      ...a,
      [contestId]: Object.keys(r[contestId]).reduce(
        (b, choiceId) => ({
          ...b,
          [choiceId]: numberify
            ? Number(r[contestId][choiceId])
            : stringifyPossibleNull(r[contestId][choiceId]),
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
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results`
  )
  if (!response) return null
  return reformatResults(response, false)
}

const useResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): [IResultValues | null, (arg0: IResultValues) => Promise<boolean>] => {
  const [results, setResults] = useState<IResultValues | null>(null)

  const updateResults = async (newResults: IResultValues): Promise<boolean> => {
    const response = await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results`,
      {
        method: 'PUT',
        // stringify and numberify the contests (all number values are handled as strings clientside, but are required as numbers serverside)
        body: JSON.stringify(numberifyResults(newResults)),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    setResults(newResults)
    return !!response
  }

  useEffect(() => {
    ;(async () => {
      const newResults = await getResults(electionId, jurisdictionId, roundId)
      setResults(newResults)
    })()
  }, [electionId, jurisdictionId, roundId])
  return [results, updateResults]
}

export default useResults

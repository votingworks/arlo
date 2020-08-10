import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../utilities'

export interface IResultValues {
  [contestId: string]: {
    [choiceId: string]: number | string
  }
}

export interface IResults {
  results: IResultValues
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

const numberifyResults = (r: IResults): IResultValues =>
  reformatResults(r.results)

const getResults = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IResults | null> => {
  try {
    const response: IResultValues = await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/results`
    )
    return { results: reformatResults(response, false) }
  } catch (err) /* istanbul ignore next */ {
    // TODO move toasting into api
    toast.error(err.message)
    return null
  }
}

const useResults = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): [IResults | null, (arg0: IResults) => Promise<boolean>] => {
  const [results, setResults] = useState<IResults | null>(null)

  const updateResults = async (newResults: IResults): Promise<boolean> => {
    if (!results) return false
    try {
      await api(
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
      const newResults = await getResults(electionId, jurisdictionId, roundId)
      setResults(newResults)
    })()
  }, [electionId, jurisdictionId, roundId])
  return [results, updateResults]
}

export default useResults

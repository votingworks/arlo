import { toast } from 'react-toastify'
import { useQuery, UseQueryResult } from 'react-query'

import { fetchApi } from '../../../utils/api'
import { IElectionResults } from './electionResults'
import { sleep } from '../../../utils/sleep'

export type AuditType = 'ballotComparison' | 'ballotPolling' | 'batchComparison'

export type SampleSizes = { [key in AuditType]: number }

export const placeholderSampleSizes: SampleSizes = {
  ballotComparison: 0,
  ballotPolling: 0,
  batchComparison: 0,
}

interface UseSampleSizesOptions {
  /** Allow introducing an artificial delay to avoid flickering loading spinners */
  minFetchDurationMs?: number
  /** Allow overriding the global onError behavior of showing a toast */
  showToastOnError?: boolean
}

export const useSampleSizes = (
  electionResults: IElectionResults,
  riskLimitPercentage: number,
  {
    minFetchDurationMs = 0,
    showToastOnError = true,
  }: UseSampleSizesOptions = {}
): UseQueryResult<SampleSizes, Error> =>
  useQuery<SampleSizes, Error>(
    ['sampleSizes', electionResults, riskLimitPercentage],
    async () => {
      const queryStartTime = new Date().getTime()
      const query = await fetchApi('/api/public/sample-sizes', {
        // Conceptually, this is a GET but we use a POST so that we can specify election results in
        // a body. Specifying election results in a query param could cause us to hit URL size
        // limits
        method: 'POST',
        body: JSON.stringify({ electionResults, riskLimitPercentage }),
        headers: { 'Content-Type': 'application/json' },
      })
      const queryEndTime = new Date().getTime()

      const queryTimeMs = queryEndTime - queryStartTime
      if (queryTimeMs < minFetchDurationMs) {
        await sleep(minFetchDurationMs - queryTimeMs)
      }

      return query
    },
    {
      onError: showToastOnError
        ? error => toast.error(error.message)
        : () => {}, // eslint-disable-line @typescript-eslint/no-empty-function
      placeholderData: placeholderSampleSizes,
      staleTime: Infinity, // Allow use of cached query results
    }
  )

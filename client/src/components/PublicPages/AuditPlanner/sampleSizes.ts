import { useQuery, UseQueryResult } from 'react-query'

import { fetchApi } from '../../../utils/api'
import { IElectionResults } from './electionResults'

const BALLOT_POLLING_SAMPLE_SIZE_KEYS = ['asn', '0.7', '0.8', '0.9'] as const
export type BallotPollingSampleSizeKey = typeof BALLOT_POLLING_SAMPLE_SIZE_KEYS[number]

export type SampleSizes = {
  BALLOT_POLLING: {
    [riskLimitPercentage: string]:
      | { [key in BallotPollingSampleSizeKey]: number }
      | { 'all-ballots': number }
  }
  BALLOT_COMPARISON: { [riskLimitPercentage: string]: number }
  BATCH_COMPARISON: { [riskLimitPercentage: string]: number }
}

interface UseSampleSizesOptions {
  /** Allow overriding the global onError behavior of showing a toast */
  showToastOnError?: boolean
}

export const useSampleSizes = (
  electionResults: IElectionResults
): UseQueryResult<SampleSizes, Error> =>
  useQuery<SampleSizes, Error>(
    ['sampleSizes', electionResults],
    async () => {
      const sampleSizes = await fetchApi('/api/public/sample-sizes', {
        // Conceptually, this is a GET but we use a POST so that we can specify election results in
        // a body. Specifying election results in a query param could cause us to hit URL size
        // limits
        method: 'POST',
        body: JSON.stringify({ electionResults }),
        headers: { 'Content-Type': 'application/json' },
      })
      return {
        BALLOT_COMPARISON: sampleSizes.ballotComparison,
        BALLOT_POLLING: sampleSizes.ballotPolling,
        BATCH_COMPARISON: sampleSizes.batchComparison,
      }
    },
    // Override default onError behavior to avoid showing a toast, since we show an inline error
    { onError: () => {} } // eslint-disable-line @typescript-eslint/no-empty-function
  )

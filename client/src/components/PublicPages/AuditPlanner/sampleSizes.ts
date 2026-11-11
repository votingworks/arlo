import { useQuery, UseQueryResult } from 'react-query'

import { ApiError, fetchApi } from '../../../utils/api'
import { IElectionResults } from './electionResults'

const BALLOT_POLLING_SAMPLE_SIZE_KEYS = ['asn', '0.7', '0.8', '0.9'] as const
export type BallotPollingSampleSizeKey =
  (typeof BALLOT_POLLING_SAMPLE_SIZE_KEYS)[number]

// A missing option means it couldn't be computed (e.g. BRAVO only computes an ASN for contests with
// multiple winners)
export type BallotPollingSampleSizeOptions =
  | { [key in BallotPollingSampleSizeKey]?: number }
  | { 'all-ballots': number }

// A null sample size means the audit type doesn't support the contest (e.g. uncontested contests)
export type SampleSizes = {
  BALLOT_POLLING: {
    [riskLimitPercentage: string]: BallotPollingSampleSizeOptions | null
  }
  BALLOT_COMPARISON: { [riskLimitPercentage: string]: number | null }
  BATCH_COMPARISON: { [riskLimitPercentage: string]: number | null }
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

export type BallotPollingMathType = 'BRAVO' | 'PROVIDENCE'

export interface IProvidenceSampleSize {
  sampleSize: BallotPollingSampleSizeOptions | null
  // Set when sampleSize is null
  unsupportedReason: string | null
}

// Providence sample sizes are computed one risk limit at a time, since each can take seconds for a
// close contest
export const useProvidenceSampleSize = (
  electionResults: IElectionResults,
  riskLimitPercentage: number,
  enabled: boolean
): UseQueryResult<IProvidenceSampleSize, ApiError> =>
  useQuery<IProvidenceSampleSize, ApiError>(
    ['providenceSampleSize', electionResults, riskLimitPercentage],
    () =>
      fetchApi('/api/public/sample-sizes/providence', {
        method: 'POST',
        body: JSON.stringify({ electionResults, riskLimitPercentage }),
        headers: { 'Content-Type': 'application/json' },
      }),
    {
      enabled,
      // Sample sizes are deterministic, so never recompute a risk limit already fetched
      staleTime: Infinity,
      // The server computes one Providence sample size at a time and answers 429 while busy, so
      // keep trying for a while; any other failure would only recur
      retry: (failureCount, error) =>
        error.statusCode === 429 && failureCount < 30,
      retryDelay: 1000,
      onError: () => {}, // eslint-disable-line @typescript-eslint/no-empty-function
    }
  )

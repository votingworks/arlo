import { toast } from 'react-toastify'
import { useQuery, UseQueryResult } from 'react-query'

import { AuditType } from '../../useAuditSettings'
import { fetchApi } from '../../../utils/api'
import { IElectionResults } from './electionResults'

export type SampleSizes = {
  [auditType in Exclude<AuditType, 'HYBRID'>]: {
    [riskLimitPercentage: string]: number
  }
}

interface UseSampleSizesOptions {
  /** Allow overriding the global onError behavior of showing a toast */
  showToastOnError?: boolean
}

export const useSampleSizes = (
  electionResults: IElectionResults,
  { showToastOnError = true }: UseSampleSizesOptions = {}
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
    {
      onError: showToastOnError
        ? error => toast.error(error.message)
        : () => {}, // eslint-disable-line @typescript-eslint/no-empty-function
    }
  )

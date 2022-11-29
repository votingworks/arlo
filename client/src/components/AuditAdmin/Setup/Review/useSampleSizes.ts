import { UseQueryOptions, useQuery, UseQueryResult } from 'react-query'
import { FileProcessingStatus } from '../../../useCSV'
import { fetchApi, ApiError } from '../../../../utils/api'

export interface ISampleSizeOption {
  size: number | null
  prob: number | null
  key: string
  // In hybrid audits only
  sizeCvr?: number
  sizeNonCvr?: number
}

export interface ISampleSizeOptions {
  [contestId: string]: ISampleSizeOption[]
}

export interface ISelectedSampleSizes {
  [contestId: string]: ISampleSizeOption
}

export interface ISampleSizesResponse {
  sampleSizes: ISampleSizeOptions | null
  selected: ISelectedSampleSizes | null
  task: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  }
}

const useSampleSizes = (
  electionId: string,
  roundNumber: number,
  options: UseQueryOptions<ISampleSizesResponse, ApiError> = {}
): UseQueryResult<ISampleSizesResponse, ApiError> =>
  useQuery<ISampleSizesResponse, ApiError>(
    ['elections', electionId, 'sample-sizes', roundNumber],
    () => fetchApi(`/api/election/${electionId}/sample-sizes/${roundNumber}`),
    options
  )

export default useSampleSizes

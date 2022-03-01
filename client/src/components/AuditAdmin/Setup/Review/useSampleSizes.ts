import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../../../utilities'
import { FileProcessingStatus } from '../../../useCSV'

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

const getSampleSizeOptions = async (
  electionId: string
): Promise<ISampleSizesResponse | null> =>
  api(`/election/${electionId}/sample-sizes`)

const useSampleSizes = (
  electionId: string,
  shouldFetch: boolean
): ISampleSizesResponse | null => {
  const [
    sampleSizeOptions,
    setSampleSizeOptions,
  ] = useState<ISampleSizesResponse | null>(null)

  useEffect(() => {
    ;(async () => {
      const isComplete = async () => {
        const response = await getSampleSizeOptions(electionId)
        if (response && response.task.completedAt !== null) {
          setSampleSizeOptions(response)
          return true
        }
        return false
      }
      if (shouldFetch)
        poll(
          isComplete,
          () => null,
          err => toast.error(err.message),
          5 * 60 * 1000 // Time out loading sample sizes after 5 minutes
        )
    })()
  }, [electionId, shouldFetch])

  return sampleSizeOptions
}

export default useSampleSizes

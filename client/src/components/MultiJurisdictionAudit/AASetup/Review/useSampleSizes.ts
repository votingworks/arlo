import { useEffect, useState } from 'react'
import { api } from '../../../utilities'

export interface ISampleSizeOption {
  size: number | null
  prob: number | null
  key: string
}

export interface ISampleSizeOptions {
  [contestId: string]: ISampleSizeOption[]
}

const loadSampleSizes = async (
  electionId: string
): Promise<ISampleSizeOptions | null> => {
  const response = await api<{ sampleSizes: ISampleSizeOptions }>(
    `/election/${electionId}/sample-sizes`
  )
  return response && response.sampleSizes
}

const useSampleSizes = (
  electionId: string,
  shouldFetch: boolean
): ISampleSizeOptions | null => {
  const [
    sampleSizeOptions,
    setSampleSizeOptions,
  ] = useState<ISampleSizeOptions | null>(null)

  useEffect(() => {
    ;(async () => {
      if (shouldFetch) setSampleSizeOptions(await loadSampleSizes(electionId))
    })()
  }, [electionId, shouldFetch])

  return sampleSizeOptions
}

export default useSampleSizes

import { useEffect, useState } from 'react'
import { api } from '../../../utilities'

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

interface ISelectedSampleSizes {
  [contestId: string]: ISampleSizeOption
}

const loadSampleSizes = async (
  electionId: string
): Promise<[ISampleSizeOptions, ISelectedSampleSizes] | null> => {
  const response = await api<{
    sampleSizes: ISampleSizeOptions
    selected: ISelectedSampleSizes
  }>(`/election/${electionId}/sample-sizes`)
  return response && [response.sampleSizes, response.selected]
}

const useSampleSizes = (
  electionId: string,
  shouldFetch: boolean
): [ISampleSizeOptions, ISelectedSampleSizes] | null => {
  const [sampleSizeOptions, setSampleSizeOptions] = useState<
    [ISampleSizeOptions, ISelectedSampleSizes] | null
  >(null)

  useEffect(() => {
    ;(async () => {
      if (shouldFetch) setSampleSizeOptions(await loadSampleSizes(electionId))
    })()
  }, [electionId, shouldFetch])

  return sampleSizeOptions
}

export default useSampleSizes

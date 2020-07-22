import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../../utilities'
import { ISampleSizeOption } from '../../../../types'

export interface IStringSampleSizeOption {
  size: string
  key: string
  prob: number | null
}

export interface IStringSampleSizeOptions {
  [key: string]: IStringSampleSizeOption[]
}

export interface ISampleSizeOptions {
  [key: string]: ISampleSizeOption[]
}

export interface ISampleSizes {
  [key: string]: string
}

const loadSampleSizes = async (
  electionId: string
): Promise<IStringSampleSizeOptions | null> => {
  try {
    const {
      sampleSizes: options,
    }: { sampleSizes: ISampleSizeOptions } = await api(
      `/election/${electionId}/sample-sizes`
    )
    return Object.keys(options).reduce(
      (a, contestId) => ({
        [contestId]: [
          ...options[contestId].map(option => ({
            ...option,
            size: `${option.size}`,
          })),
          { key: 'custom', size: '', prob: null },
        ],
        ...a,
      }),
      {}
    )
  } catch (err) {
    toast.error(err.message)
    return null
  }
}

const putSampleSizes = async (
  electionId: string,
  sampleSizes: ISampleSizes
): Promise<boolean> => {
  try {
    await api(`/election/${electionId}/round`, {
      method: 'POST',
      body: JSON.stringify({
        sampleSizes: {
          // converts to number so it submits in the form: { [key: string]: number }
          ...Object.keys(sampleSizes).reduce(
            (a, v) => ({
              ...a,
              [v]: Number(sampleSizes[v]),
            }),
            {}
          ),
        },
        roundNum: 1,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return true
  } catch (err) {
    toast.error(err.message)
    return false
  }
}

const useSampleSizes = (
  electionId: string
): [
  IStringSampleSizeOptions | null,
  (sampleSizes: ISampleSizes) => Promise<boolean>
] => {
  const [
    sampleSizeOptions,
    setSampleSizeOptions,
  ] = useState<IStringSampleSizeOptions | null>(null)

  const uploadSampleSizes = async (sizes: ISampleSizes): Promise<boolean> => {
    // TODO poll for result of upload
    if (await putSampleSizes(electionId, sizes)) {
      setSampleSizeOptions(await loadSampleSizes(electionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      setSampleSizeOptions(await loadSampleSizes(electionId))
    })()
  }, [electionId])

  return [sampleSizeOptions, uploadSampleSizes]
}

export default useSampleSizes

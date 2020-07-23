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
  [contestId: string]: IStringSampleSizeOption[]
}

export interface ISampleSizeOptions {
  [contestId: string]: ISampleSizeOption[]
}

export interface IStringSampleSizes {
  [contestId: string]: string
}

export interface ISampleSizes {
  [contestId: string]: number
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
  stringSampleSizes: IStringSampleSizes
): Promise<boolean> => {
  try {
    const sampleSizes: ISampleSizes = {
      // converts to number so it submits in the form: { [contestId: string]: number }
      ...Object.keys(stringSampleSizes).reduce(
        (a, v) => ({
          ...a,
          [v]: Number(stringSampleSizes[v]),
        }),
        {}
      ),
    }
    await api(`/election/${electionId}/round`, {
      method: 'POST',
      body: JSON.stringify({
        sampleSizes,
        roundNum: 1,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return true
  } catch (err) /* istanbul ignore next */ {
    // TEST TODO move toast handling to api
    toast.error(err.message)
    return false
  }
}

const useSampleSizes = (
  electionId: string
): [
  IStringSampleSizeOptions | null,
  (sampleSizes: IStringSampleSizes) => Promise<boolean>
] => {
  const [
    sampleSizeOptions,
    setSampleSizeOptions,
  ] = useState<IStringSampleSizeOptions | null>(null)

  const uploadSampleSizes = async (
    sizes: IStringSampleSizes
  ): Promise<boolean> => {
    // TODO poll for result of upload
    /* istanbul ignore else */
    if (await putSampleSizes(electionId, sizes)) {
      return true
    }
    /* istanbul ignore next */
    // TEST TODO included with above
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

import * as Yup from 'yup'
import { Params } from '../types'

export const api = async <T>(
  endpoint: string,
  { electionId, ...options }: Params & RequestInit
): Promise<T> => {
  const apiBaseURL = electionId ? `/election/${electionId}` : ''
  const res = await fetch(apiBaseURL + endpoint, options)
  if (!res.ok) {
    throw new Error(res.statusText)
  }
  return res.json() as Promise<T>
}

export const poll = (
  condition: () => Promise<boolean>,
  callback: () => void,
  errback: (arg0: Error) => void,
  timeout: number = 120000,
  interval: number = 1000
) => {
  const endTime = Date.now() + timeout
  ;(async function p() {
    const done = await condition()
    if (done) {
      callback()
    } else if (Date.now() < endTime) {
      setTimeout(p, interval)
    } else {
      errback(new Error(`Timed out`))
    }
  })()
}

const numberSchema = Yup.number()
  .typeError('Must be a number')
  .integer('Must be an integer')
  .min(0, 'Must be a positive number')
  .required('Required')

export const testNumber = (
  max?: number,
  message?: string
): ((value: number) => Promise<string | undefined>) => {
  const schema = max
    ? numberSchema.concat(
        Yup.number().max(max, message || `Must be smaller than ${max}`)
      )
    : numberSchema

  return async (value: unknown) => {
    try {
      await schema.validate(value)
    } catch (error) {
      return error.errors[0]
    }
  }
}

export const asyncForEach = async <T>(
  array: T[],
  callback: (value: T, index: number, array: T[]) => Promise<void>
) => {
  for (let index = 0; index < array.length; index++) {
    await callback(array[index], index, array)
  }
}

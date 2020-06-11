import { toast } from 'react-toastify'
import number from '../utils/number-schema'
import { IErrorResponse } from '../types'

const tryJson = (responseText: string) => {
  try {
    return JSON.parse(responseText)
  } catch (err) {
    return {}
  }
}

export const api = async <T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> => {
  const response = await fetch(endpoint, options)
  if (!response.ok) {
    const responseText = await response.text()
    const { errors } = tryJson(responseText)
    const error =
      errors && errors.length ? errors[0] : { message: response.statusText }
    const errorData = { ...error, responseText, response }
    console.error(responseText) // eslint-disable-line no-console
    throw errorData
  }
  return response.json() as Promise<T>
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
    const time = Date.now()
    try {
      const done = await condition()
      if (done) {
        callback()
      } else if (time < endTime) {
        setTimeout(p, interval)
      } else {
        errback(new Error(`Timed out`))
      }
    } catch (err) {
      errback(err)
    }
  })()
}

const numberSchema = number()
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
        number().max(max, message || `Must be smaller than ${max}`)
      )
    : numberSchema

  return async (value: unknown) => {
    try {
      await schema.validate(value)
      return undefined
    } catch (error) {
      return error.errors[0]
    }
  }
}

export const asyncForEach = async <T>(
  array: T[],
  callback: (value: T, index: number, array: T[]) => Promise<void>
) => {
  for (let index = 0; index < array.length; index += 1) {
    // eslint-disable-next-line no-await-in-loop
    await callback(array[index], index, array)
  }
}

const getErrorsFromResponse = (
  response: unknown
): { message: string }[] | undefined => {
  if (typeof response !== 'object' || !response) {
    return undefined
  }

  const { errors } = response as { [key: string]: unknown }

  if (!Array.isArray(errors)) {
    return undefined
  }

  return errors
}

export const checkAndToast = (
  response: unknown
): response is IErrorResponse => {
  const errors = getErrorsFromResponse(response)
  if (errors) {
    toast.error(
      `There was a server error regarding: ${errors
        .map(({ message }) => message)
        .join(', ')}`
    )
    return true
  }
  return false
}

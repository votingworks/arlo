import { useRef, useEffect } from 'react'
import { toast } from 'react-toastify'
import number from '../utils/number-schema'
import { IErrorResponse } from '../types'

export const tryJson = (responseText: string) => {
  try {
    return JSON.parse(responseText)
  } catch (err) {
    return {}
  }
}

export const api = async <T>(
  endpoint: string,
  options?: RequestInit
): Promise<T | null> => {
  try {
    const response = await fetch(`/api${endpoint}`, options)
    if (!response.ok) {
      // If we get a 401, it most likely means the session expired, so we
      // redirect to the login screen with a flag to show a message.
      if (response.status === 401) {
        window.location.assign(
          encodeURI(
            '/?error=unauthorized&message=You have been logged out due to inactivity.'
          )
        )
        return null
      }

      const responseText = await response.text()
      const { errors } = tryJson(responseText)
      const error =
        errors && errors.length ? errors[0] : { message: response.statusText }
      const errorData = { ...error, responseText, response }
      console.error(responseText) // eslint-disable-line no-console
      throw errorData
    }
    return response.json() as Promise<T>
  } catch (err) {
    toast.error(err.message)
    return null
  }
}

export const apiDownload = (endpoint: string) =>
  new Promise((resolve, reject) => {
    fetch(`/api${endpoint}`)
      .then(async response => {
        if (!response) {
          throw new Error('bad response')
        }
        const respHeaders: string | null = response.headers.get(
          'content-disposition'
        )
        const [, filename]: string[] = respHeaders
          ? respHeaders.split('"')
          : ['']
        const blobRes = await response.blob()
        return { filename, blobRes }
      })
      .then(({ filename, blobRes }) => {
        const url: string = window.URL.createObjectURL(new Blob([blobRes]))
        const link: HTMLAnchorElement = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename) // or any other extension
        document.body.appendChild(link)
        link.click()
        link.parentNode!.removeChild(link)
        resolve({ status: 'ok' })
      })
      .catch(err => reject(err))
  })

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

// https://overreacted.io/making-setinterval-declarative-with-react-hooks/
/* istanbul ignore next */
export const useInterval = (
  callback: Function,
  delay: number | null,
  callImmediately?: boolean
) => {
  const savedCallback = useRef<Function>()

  // Remember the latest function.
  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  // Set up the interval.
  useEffect(/* eslint consistent-return: "off" */
  () => {
    function tick() {
      savedCallback.current!()
    }
    if (callImmediately) tick()
    if (delay !== null) {
      // allows for pausing
      const id = setInterval(tick, delay)
      return () => clearInterval(id)
    }
  }, [delay, callImmediately])
}

/** https://stackoverflow.com/questions/6229197/how-to-know-if-two-arrays-have-the-same-values/55614659#55614659
 * assumes array elements are primitive types
 * check whether 2 arrays are equal sets.
 * @param  {} a1 is an array
 * @param  {} a2 is an array
 */
/* istanbul ignore next */
export const areArraysEqualSets = (a1: unknown[], a2: unknown[]): boolean => {
  const superSet: { [key: string]: number } = {}
  for (const i of a1) {
    const e = i + typeof i
    superSet[e] = 1
  }

  for (const i of a2) {
    const e = i + typeof i
    if (!superSet[e]) {
      return false
    }
    superSet[e] = 2
  }

  for (const e in superSet) {
    if (superSet[e] === 1) {
      return false
    }
  }

  return true
}

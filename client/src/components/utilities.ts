import { useRef, useEffect } from 'react'
import { toast } from 'react-toastify'
import number from '../utils/number-schema'
import { addCSRFToken, tryJson } from '../utils/api'

export const parseApiError = async (response: Response) => {
  const responseText = await response.text()
  const { errors } = tryJson(responseText)
  const error =
    errors && errors.length ? errors[0] : { message: response.statusText }
  return { ...error, responseText, response }
}

// Deprecated - use utils/api.fetchApi with react-query
export const api = async <T>(
  endpoint: string,
  options?: RequestInit
): Promise<T | null> => {
  try {
    const response = await fetch(`/api${endpoint}`, addCSRFToken(options))
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

      const error = await parseApiError(response)
      console.error(error.responseText) // eslint-disable-line no-console
      throw error
    }
    const text = await response.text()
    // console.log(endpoint, response.status, text)
    return JSON.parse(text)
    // return response.json() as Promise<T>
  } catch (err) {
    toast.error(
      err.errorType === 'Internal Server Error'
        ? 'Something went wrong. Please try again or contact support.'
        : err.message
    )
    return null
  }
}

export const apiDownload = (endpoint: string) =>
  new Promise((resolve, reject) => {
    try {
      const windowObj = window.open(`/api${endpoint}`)
      if (windowObj != null) {
        windowObj.onbeforeunload = () => {
          resolve('done')
        }
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err)
      reject(err)
    }
  })

export const downloadFile = (fileBlob: Blob, fileName?: string) => {
  const a = document.createElement('a')
  document.body.appendChild(a)
  a.href = URL.createObjectURL(fileBlob)
  a.download = fileName || ''
  a.click()
  document.body.removeChild(a)
}

// Deprecated - use react-query's refetch interval
export const poll = (
  condition: () => Promise<boolean>,
  callback: () => void,
  errback: (arg0: Error) => void,
  timeout = 120000,
  interval = 1000
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
  useEffect(
    /* eslint consistent-return: "off" */
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
    },
    [delay, callImmediately]
  )
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

// From https://usehooks-typescript.com/react-hook/use-is-mounted
export const useIsMounted = () => {
  const isMounted = useRef(false)

  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])

  return () => isMounted.current
}

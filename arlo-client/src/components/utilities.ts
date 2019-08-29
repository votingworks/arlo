import { Params } from '../types'

export const api = <T>(
  endpoint: string,
  { electionId, ...options }: Params & RequestInit
): Promise<T> => {
  const apiBaseURL = electionId ? `/election/${electionId}` : ''
  return fetch(apiBaseURL + endpoint, options).then(res => {
    if (!res.ok) {
      throw new Error(res.statusText)
    }
    return res.json() as Promise<T>
  })
}

export const poll = (
  condition: () => Promise<boolean>,
  callback: () => any,
  errback: (arg0: Error) => void,
  timeout: number = 60000,
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

export default api

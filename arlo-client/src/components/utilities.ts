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
  condition: () => boolean,
  action: () => void,
  callback: () => any,
  errback: (arg0: Error) => void,
  timeout: number = 2000,
  interval: number = 100
) => {
  const endTime = Number(new Date()) + timeout
  ;(function p() {
    action()
    if (condition()) {
      callback()
    } else if (Number(new Date()) < endTime) {
      setTimeout(p, interval)
    } else {
      errback(new Error(`Timed out for ${condition}: ${arguments}`))
    }
  })()
}

export default api

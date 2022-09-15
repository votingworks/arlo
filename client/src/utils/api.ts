import { AxiosRequestConfig } from 'axios'

const parseCookies = () =>
  Object.fromEntries(
    document.cookie.split(';').map(pair => pair.trim().split('='))
  )

export const addCSRFToken = <T extends RequestInit | AxiosRequestConfig>(
  options?: T
): T | undefined => {
  const token = parseCookies()._csrf_token
  if (
    token &&
    options &&
    ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method!)
  )
    return {
      ...options,
      headers: { ...options.headers, 'X-CSRFToken': token },
    }
  return options
}

export const tryJson = (responseText: string): ReturnType<JSON['parse']> => {
  try {
    return JSON.parse(responseText)
  } catch (err) {
    return {}
  }
}
export class ApiError extends Error {
  public statusCode: number

  public constructor(message: string, statusCode: number) {
    super(message)
    this.statusCode = statusCode
  }
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const fetchApi = async (url: string, options?: RequestInit) => {
  const response = await fetch(url, addCSRFToken(options))
  if (response.ok) return response.json()
  const text = await response.text()
  const { errors } = tryJson(text)
  const error = errors && errors.length && errors[0].message
  throw new ApiError(error || text, response.status)
}

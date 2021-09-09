import axios, { AxiosRequestConfig } from 'axios'
import React from 'react'
import { createLocation, createMemoryHistory, MemoryHistory } from 'history'
import { match as routerMatch, Router } from 'react-router-dom'
import equal from 'fast-deep-equal'
import { render } from '@testing-library/react'

type MatchParameter<Params> = { [K in keyof Params]?: string }

const generateUrl = <Params extends MatchParameter<Params>>(
  path: string,
  params: Params
): string => {
  let tempPath = path

  for (const param in params) {
    /* istanbul ignore else */
    if (Object.prototype.hasOwnProperty.call(params, param)) {
      const value = params[param]
      tempPath = tempPath.replace(`:${param}`, value as NonNullable<
        typeof value
      >)
    }
  }

  return tempPath
}

/** Credit to https://stackoverflow.com/a/56452779 for solution to mocking React Router props */

export const routerTestProps = <Params extends MatchParameter<Params> = {}>(
  path: string,
  params: Params
) => {
  const match: routerMatch<Params> = {
    isExact: false,
    path,
    url: generateUrl(path, params),
    params,
  }
  const history = createMemoryHistory()
  const location = createLocation(match.url)

  return { history, location, match }
}

// Copied from https://testing-library.com/docs/example-react-router
export const renderWithRouter = (
  ui: React.ReactElement,
  {
    route = '/',
    history = createMemoryHistory({ initialEntries: [route] }),
  }: { route?: string; history?: MemoryHistory } = {}
) => {
  const Wrapper: React.FC = ({ children }: { children?: React.ReactNode }) => (
    <Router history={history}>{children}</Router>
  )

  return {
    ...render(ui, { wrapper: Wrapper }),
    // Adding `history` to the returned utilities to allow us
    // to reference it in our tests (just try to avoid using
    // this to test implementation details).
    history,
  }
}

// withMockFetch is a helper to mock calls to external APIs (e.g. the Arlo backend).
// - It takes an array of expected FetchRequests and a test runner function
// - It mocks window.fetch to return the given response for each request
// - After running the test function, it checks that the actual received
//   requests exactly match the expected requests.

interface FetchRequest {
  url: string
  options?: RequestInit
  response: object | null
  error?: {
    status: number
    statusText: string
  }
}

const isEqualRequestBody = (
  body1?: BodyInit | null,
  body2?: BodyInit | null
) => {
  const formDataToObject = (body?: BodyInit | null) =>
    body instanceof FormData
      ? Object.fromEntries(
          [...body.entries()].map(([key, value]) => [
            key,
            value instanceof File
              ? {
                  name: value.name,
                  type: value.type,
                }
              : value,
          ])
        )
      : body
  return equal(formDataToObject(body1), formDataToObject(body2))
}

export const withMockFetch = async (
  requests: FetchRequest[],
  testFn: () => Promise<void>
) => {
  const requestsLeft = [...requests]
  const mockFetch = jest.fn(async (url: string, options: RequestInit = {}) => {
    const [expectedRequest] = requestsLeft.splice(0, 1)
    const expectedOptions = expectedRequest.options || {}
    if (
      expectedRequest &&
      expectedRequest.url === url &&
      expectedOptions.method === options.method &&
      equal(expectedOptions.headers, options.headers) &&
      isEqualRequestBody(expectedOptions.body, options.body)
    ) {
      return expectedRequest.error
        ? new Response(
            JSON.stringify(expectedRequest.response),
            expectedRequest.error
          )
        : new Response(JSON.stringify(expectedRequest.response))
    }

    if (expectedRequest) {
      const requestIndex = requests.length - requestsLeft.length - 1
      // eslint-disable-next-line no-console
      console.error(
        `Expected fetch request (${requestIndex}):\n`,
        expectedRequest,
        '\nActual fetch request:\n',
        { url, options }
      )
    } else {
      // eslint-disable-next-line no-console
      console.error('Unexpected extra fetch request:\n', { url, options })
    }
    return new Response(JSON.stringify(null))
  })

  // Set up fetch mock
  window.fetch = mockFetch as typeof window.fetch

  // Also mock axios, since we use that in some cases
  // To enable axios mock, the test file must have jest.mock('axios') at the top
  if ('mockImplementation' in (axios as any).default) {
    ;(axios as any).mockImplementation(
      async (
        url: string,
        { onUploadProgress, data, ...options }: AxiosRequestConfig
      ) => {
        if (onUploadProgress) onUploadProgress({ loaded: 1, total: 2 })
        mockFetch(url, { ...options, body: data })
      }
    )
  }

  await testFn()

  const actualRequests = mockFetch.mock.calls.map(([url, options]) => ({
    url,
    options,
  }))
  const expectedRequests = requests.map(({ url, options }) => ({
    url,
    options,
  }))
  expect(actualRequests).toEqual(expectedRequests)
}

export const regexpEscape = (s: string) => {
  /* eslint-disable no-useless-escape */
  return s.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')
}

export default {
  routerTestProps,
}

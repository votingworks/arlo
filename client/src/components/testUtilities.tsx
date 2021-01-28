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
  skipBody?: boolean
  error?: {
    status: number
    statusText: string
  }
}

export const withMockFetch = async (
  requests: FetchRequest[],
  testFn: () => Promise<void>
) => {
  const requestsLeft = [...requests]
  const mockFetch = jest.fn(async (url: string, options?: RequestInit) => {
    const [expectedRequest] = requestsLeft.splice(0, 1)
    if (
      expectedRequest &&
      expectedRequest.url === url
      // equal(expectedRequest.options, options)
      // (expectedRequest.skipBody || equal(expectedRequest.options, options))
    ) {
      if (
        expectedRequest.options &&
        expectedRequest.options.body instanceof FormData &&
        options &&
        options.body &&
        options.body instanceof FormData
      ) {
        const expectedData = expectedRequest.options.body
        const receivedData = options.body
        // defined expectedData and receivedData here because TS won't recognize the typechecks above
        // when expectedRequest.options.body and options.body are used in the loop
        const fileNamesMatch: boolean = Array.from(expectedData.keys())
          .map(key => {
            const expectedFile = expectedData.get(key) as File // the only time we ever send a FormData is when submitting a File
            const receivedFile = receivedData.get(key) as File
            if (expectedFile.name === receivedFile.name) {
              return true
            }
            return false
          })
          .every(v => v) // treating it as a list even though we only send one at a time because we don't know the key that will be used
        if (fileNamesMatch)
          return new Response(JSON.stringify(expectedRequest.response))
      } else if (equal(expectedRequest.options, options)) {
        return expectedRequest.error
          ? new Response(
              JSON.stringify(expectedRequest.response),
              expectedRequest.error
            )
          : new Response(JSON.stringify(expectedRequest.response))
      }
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
    return new Response(JSON.stringify({}))
  })
  window.fetch = mockFetch as typeof window.fetch

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

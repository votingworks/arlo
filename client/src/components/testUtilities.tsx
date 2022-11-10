import axios, { AxiosRequestConfig, AxiosError } from 'axios'
import React from 'react'
import { createLocation, createMemoryHistory, MemoryHistory } from 'history'
import { match as routerMatch, Router } from 'react-router-dom'
import equal from 'fast-deep-equal'
import {
  render,
  screen,
  within,
  waitFor,
  RenderResult,
  Queries,
  Matcher,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, DefaultOptions } from 'react-query'
import { queryClientDefaultOptions } from '../App'
import { assert } from './utilities'

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
      tempPath = tempPath.replace(
        `:${param}`,
        value as NonNullable<typeof value>
      )
    }
  }

  return tempPath
}

/** Credit to https://stackoverflow.com/a/56452779 for solution to mocking React Router props */
// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types, @typescript-eslint/ban-types
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

type RenderWithRouterReturn = RenderResult<Queries> & {
  history: MemoryHistory
}

// Copied from https://testing-library.com/docs/example-react-router
export function renderWithRouter(
  ui: React.ReactElement,
  {
    route = '/',
    history = createMemoryHistory({ initialEntries: [route] }),
  }: { route?: string; history?: MemoryHistory } = {}
): RenderWithRouterReturn {
  const Wrapper: React.FC = ({ children }: { children?: React.ReactNode }) => (
    <Router history={history}>{children}</Router>
  )

  return {
    ...render(ui, { wrapper: Wrapper }),
    // Adding `history` to the returned utilities to allow us
    // to reference it in our tests (just try to avoid using
    // this to test implementation details).
    history,
  } as RenderWithRouterReturn
}

// withMockFetch is a helper to mock calls to external APIs (e.g. the Arlo backend).
// - It takes an array of expected FetchRequests and a test runner function
// - It mocks window.fetch to return the given response for each request
// - After running the test function, it checks that the actual received
//   requests exactly match the expected requests.

interface FetchRequest {
  url: string
  options?: RequestInit
  // eslint-disable-next-line @typescript-eslint/ban-types
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
  const unpackFormData = (body?: BodyInit | null) => {
    if (body instanceof FormData) {
      return [...body.entries()].map(([key, value]) => [
        key,
        value instanceof File ? { name: value.name, type: value.type } : value,
      ])
    }
    return body
  }
  return equal(unpackFormData(body1), unpackFormData(body2))
}

export const withMockFetch = async (
  requests: FetchRequest[],
  testFn: () => Promise<void>
): Promise<void> => {
  const requestsLeft = [...requests]
  const mockFetch = jest.fn(async (url: string, options: RequestInit = {}) => {
    const [expectedRequest] = requestsLeft.splice(0, 1)
    if (!expectedRequest) {
      // eslint-disable-next-line no-console
      console.error('Unexpected extra fetch request:\n', { url, options })
      return new Response(JSON.stringify(null))
    }

    const expectedOptions = expectedRequest.options || {}
    if (
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

    const requestIndex = requests.length - requestsLeft.length - 1
    // eslint-disable-next-line no-console
    console.error(
      `Expected fetch request (${requestIndex}):\n`,
      expectedRequest,
      '\nActual fetch request:\n',
      { url, options }
    )
    return new Response(JSON.stringify(null))
  })

  // Set up fetch mock
  window.fetch = mockFetch as typeof window.fetch

  // Also mock axios, since we use that in some cases
  // To enable axios mock, the test file must have jest.mock('axios') at the top
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ('mockImplementation' in (axios as any).default) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(axios as any).mockImplementation(
      async (
        url: string,
        { onUploadProgress, data, ...options }: AxiosRequestConfig
      ) => {
        if (onUploadProgress) onUploadProgress({ loaded: 1, total: 2 })
        const response = await mockFetch(url, { ...options, body: data })
        if (response.status >= 400) {
          const error = new Error() as AxiosError
          error.response = {
            config: {},
            ...response,
            data: JSON.parse(await response.text()),
          }
          throw error
        }
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

export const serverError = (
  name: string,
  apiCall: { url: string; options?: RequestInit }
): FetchRequest => ({
  ...apiCall,
  response: {
    errors: [
      { errorType: 'Server Error', message: `something went wrong: ${name}` },
    ],
  },
  error: { status: 500, statusText: 'Server Error' },
})

export const regexpEscape = (s: string): string => {
  /* eslint-disable no-useless-escape */
  return s.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')
}

// It's important to close the toast after checking it so there's no rendering
// happen after the test ends
export const findAndCloseToast = async (
  expectedContent: string
): Promise<void> => {
  const toastBody = await screen.findByRole('alert')
  expect(toastBody).toHaveTextContent(expectedContent)
  const toast = toastBody.closest('div.Toastify__toast')! as HTMLElement
  userEvent.click(within(toast).getByRole('button', { name: 'close' }))
  await waitFor(() =>
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  )
}

// Enforces the value type for an object with values of type Mock, while
// inferring the keys. This allows for good autocompletion of mocks in tests
// while still enforcing their type.
// Example: const mockNumbers = mocksOfType<number>()({ 'one': 1, 'two': 2 })
// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const mocksOfType = <T,>() => <Mock,>(mock: { [K in keyof Mock]: T }) =>
  mock

// Create a react-query query client with the same defaults as the app (and a few test-specific exceptions).
export const createQueryClient = (): QueryClient =>
  new QueryClient({
    defaultOptions: {
      ...queryClientDefaultOptions,
      queries: {
        ...queryClientDefaultOptions.queries,
        // Turn off query retries since those make it hard to test query error handling
        retry: false,
        // Cache query results forever to make sure we explicitly invalidate queries that we want to reload
        staleTime: Infinity,
      },
    } as DefaultOptions<unknown>,
  })

/**
 * Type a code into a CodeInput element (see Atoms/CodeInput.tsx)
 */
export const typeCode = (codeInputElement: HTMLElement, code: string): void => {
  const digitInputs = within(codeInputElement).getAllByRole('textbox')
  assert(code.length <= digitInputs.length)
  code.split('').forEach((digit, index) => {
    userEvent.type(digitInputs[index], digit)
  })
}

/**
 * A react-testing-library util for querying by text even when text is split by HTML tags
 *
 * <span>Today is <strong>Friday<strong>!</span>
 *
 * screen.getByText('Today is Friday!') --> Error
 * screen.getByText(hasTextAcrossElements('Today is Friday!')) --> No error
 */
export function hasTextAcrossElements(text: string): Matcher {
  return (content: string, node: Element | null) => {
    function hasText(n: Element) {
      return n.textContent === text
    }
    const nodeHasText = node ? hasText(node) : false
    const childrenDoNotHaveText = Array.from(node?.children || []).every(
      child => !hasText(child)
    )
    return nodeHasText && childrenDoNotHaveText
  }
}

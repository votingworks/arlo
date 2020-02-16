import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import { RouteComponentProps, BrowserRouter as Router } from 'react-router-dom'
import CreateAudit, { IElections } from './CreateAudit'
import { ICreateAuditParams } from '../types'
import { routerTestProps } from './testUtilities'
import * as utilities from './utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation(
  async (
    endpoint: string
  ): Promise<IElections | { electionId: string } | undefined> => {
    switch (endpoint) {
      case '/election/new':
        return { electionId: '1' }
      case '/elections':
        return {
          elections: [
            {
              name: 'Election One',
              id: 'election-1',
              date: 'Thu, 18 Jul 2019 16:34:07 GMT',
            },
          ],
        }
      default:
        return undefined
    }
  }
)
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

const routeProps: RouteComponentProps<ICreateAuditParams> = routerTestProps(
  '/election/:electionId',
  {
    electionId: '1',
  }
)

const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

const historySpy = jest.spyOn(routeProps.history, 'push').mockImplementation()

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
  toastSpy.mockClear()
  historySpy.mockClear()
})

describe('CreateAudit', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Router>
        <CreateAudit {...routeProps} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('calls the /election/new endpoint', async () => {
    const { getByText } = render(
      <Router>
        <CreateAudit {...routeProps} />
      </Router>
    )

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(apiMock.mock.calls[0][0]).toBe('/elections')
      expect(apiMock.mock.calls[1][0]).toBe('/election/new')
      expect(historySpy).toBeCalledTimes(1)
      expect(historySpy.mock.calls[0][0]).toBe('/election/1')
    })
  })

  it('handles error responses from server', async () => {
    checkAndToastMock.mockReturnValue(true)
    const { getByText } = render(
      <Router>
        <CreateAudit {...routeProps} />
      </Router>
    )

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(apiMock.mock.calls[0][0]).toBe('/elections')
      expect(apiMock.mock.calls[1][0]).toBe('/election/new')
      expect(checkAndToastMock).toBeCalledTimes(2)
      expect(historySpy).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(0)
    })
  })

  it('handles 404 responses from server', async () => {
    apiMock.mockImplementation(async () => {
      throw new Error('404')
    })
    checkAndToastMock.mockReturnValue(true)
    const { getByText } = render(
      <Router>
        <CreateAudit {...routeProps} />
      </Router>
    )

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(apiMock.mock.calls[0][0]).toBe('/elections')
      expect(apiMock.mock.calls[1][0]).toBe('/election/new')
      expect(checkAndToastMock).toBeCalledTimes(0)
      expect(historySpy).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(2)
    })
  })
})

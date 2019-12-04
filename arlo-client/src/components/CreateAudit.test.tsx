import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import { RouteComponentProps } from 'react-router-dom'
import CreateAudit from './CreateAudit'
import { ICreateAuditParams } from '../types'
import { routerTestProps } from './testUtilities'
import { api, checkAndToast } from './utilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>
const checkAndToastMock = checkAndToast as jest.Mock<
  ReturnType<typeof checkAndToast>,
  Parameters<typeof checkAndToast>
>

jest.mock('./utilities')

checkAndToastMock.mockImplementation(() => false)

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
    const { container } = render(<CreateAudit {...routeProps} />)
    expect(container).toMatchSnapshot()
  })

  it('calls the /election/new endpoint', async () => {
    apiMock.mockImplementation(async () => ({ electionId: '1' }))
    const { getByText } = render(<CreateAudit {...routeProps} />)

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/election/new')
      expect(historySpy).toBeCalledTimes(1)
      expect(historySpy.mock.calls[0][0]).toBe('/election/1')
    })
  })

  it('handles error responses from server', async () => {
    apiMock.mockImplementation(async () => ({ electionId: '1' }))
    checkAndToastMock.mockImplementation(() => true)
    const { getByText } = render(<CreateAudit {...routeProps} />)

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/election/new')
      expect(checkAndToastMock).toBeCalledTimes(1)
      expect(historySpy).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(0)
    })
  })

  it('handles 404 responses from server', async () => {
    apiMock.mockImplementation(async () => {
      throw new Error('404')
    })
    checkAndToastMock.mockImplementation(() => true)
    const { getByText } = render(<CreateAudit {...routeProps} />)

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/election/new')
      expect(checkAndToastMock).toBeCalledTimes(0)
      expect(historySpy).toBeCalledTimes(0)
      expect(toastSpy).toBeCalledTimes(1)
    })
  })
})

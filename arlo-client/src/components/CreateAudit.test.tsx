import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { RouteComponentProps } from 'react-router-dom'
import CreateAudit from './CreateAudit'
import { Params } from '../types'
import { routerTestProps } from './testUtilities'
import api from './utilities'

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('./utilities')

const routeProps: RouteComponentProps<Params> = routerTestProps(
  '/election/:electionId',
  {
    electionId: '1',
  }
)

afterEach(() => {
  apiMock.mockClear()
})

describe('CreateAudit', () => {
  it('renders correctly', () => {
    const { container } = render(<CreateAudit {...routeProps} />)
    expect(container).toMatchSnapshot()
  })

  it('calls the /election/new endpoint', async () => {
    apiMock.mockImplementation(async () => ({ electionId: '1' }))
    const historySpy = jest
      .spyOn(routeProps.history, 'push')
      .mockImplementation()
    const { getByText } = render(<CreateAudit {...routeProps} />)

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/election/new')
      expect(historySpy).toBeCalledTimes(1)
      expect(historySpy.mock.calls[0][0]).toBe('/election/1')
    })
  })
})

import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import { RouteComponentProps, BrowserRouter as Router } from 'react-router-dom'
import CreateAudit from './CreateAudit'
import { ICreateAuditParams } from '../types'
import { routerTestProps } from './testUtilities'
import * as utilities from './utilities'
import AuthDataProvider from './UserContext'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

const routeProps: RouteComponentProps<ICreateAuditParams> = routerTestProps(
  '/audit/:electionId',
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

  it('calls the /election/new endpoint for nonauthenticated user', async () => {
    apiMock.mockImplementation(async () => ({ electionId: '1' }))
    const { getByText, getByLabelText } = render(
      <CreateAudit {...routeProps} />
    )

    fireEvent.change(getByLabelText('Give your new audit a unique name.'), {
      target: { value: 'Audit Name' },
    })

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock).toHaveBeenNthCalledWith(1, '/election/new', {
        method: 'POST',
        body: JSON.stringify({
          auditName: 'Audit Name',
          isMultiJurisdiction: false,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      expect(historySpy).toBeCalledTimes(1)
      expect(historySpy).toHaveBeenNthCalledWith(1, '/audit/1/setup')
    })
  })

  it('requires an audit name', async () => {
    apiMock.mockImplementation(async () => ({ electionId: '1' }))
    const { getByText } = render(<CreateAudit {...routeProps} />)

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(getByText('Required')).toBeTruthy()
      expect(apiMock).toBeCalledTimes(0)
    })
  })

  it('calls the /election/new endpoint for authenticated user', async () => {
    apiMock
      .mockImplementationOnce(async () => ({
        type: 'audit_admin',
        name: 'Joe',
        email: 'test@email.org',
        jurisdictions: [],
        organizations: [
          {
            id: 'org-id',
            name: 'State',
            elections: [],
          },
        ],
      }))
      .mockImplementationOnce(async () => ({ electionId: '1' }))
    const { getByText, getByLabelText } = render(
      <AuthDataProvider>
        <CreateAudit {...routeProps} />
      </AuthDataProvider>
    )

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock).toHaveBeenNthCalledWith(1, '/auth/me')
    })
    fireEvent.change(getByLabelText('Give your new audit a unique name.'), {
      target: { value: 'Audit Name' },
    })
    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(apiMock).toHaveBeenNthCalledWith(2, '/election/new', {
        method: 'POST',
        body: JSON.stringify({
          organizationId: 'org-id',
          auditName: 'Audit Name',
          isMultiJurisdiction: true,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      expect(historySpy).toBeCalledTimes(1)
      expect(historySpy).toHaveBeenNthCalledWith(1, '/election/1/setup')
    })
  })

  it('lists associated elections for authenticated AA user', async () => {
    apiMock.mockImplementationOnce(async () => ({
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [],
      organizations: [
        {
          id: 'org-id',
          name: 'State',
          elections: [
            {
              id: 'election-1',
              auditName: '',
              state: 'NY',
            },
            {
              id: 'election-2',
              auditName: 'Election Two',
              state: 'FL',
            },
            {
              id: 'election-3',
              auditName: 'Election Three',
              state: '',
            },
            {
              id: 'election-4',
              auditName: 'Election Four',
              state: 'WA',
            },
          ],
        },
      ],
    }))
    const { container } = render(
      <Router>
        <AuthDataProvider>
          <CreateAudit {...routeProps} />
        </AuthDataProvider>
      </Router>
    )

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock).toHaveBeenNthCalledWith(1, '/auth/me')
      expect(container).toMatchSnapshot()
    })
  })

  it('lists associated elections for authenticated JA user', async () => {
    apiMock.mockImplementationOnce(async () => ({
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [
        {
          id: 'jurisdiction-1',
          name: 'County One',
          election: {
            id: 'election-1',
            auditName: 'Election One',
            state: 'NY',
          },
        },
        {
          id: 'jurisdiction-2',
          name: 'County Two',
          election: {
            id: 'election-2',
            auditName: '',
            state: '',
          },
        },
      ],
      organizations: [],
    }))
    const { container } = render(
      <Router>
        <AuthDataProvider>
          <CreateAudit {...routeProps} />
        </AuthDataProvider>
      </Router>
    )

    await wait(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock).toHaveBeenNthCalledWith(1, '/auth/me')
      expect(container).toMatchSnapshot()
    })
  })

  it('handles error responses from server', async () => {
    apiMock.mockImplementation(async () => ({ electionId: '1' }))
    checkAndToastMock.mockReturnValue(true)
    const { getByText, getByLabelText } = render(
      <CreateAudit {...routeProps} />
    )

    fireEvent.change(getByLabelText('Give your new audit a unique name.'), {
      target: { value: 'Audit Name' },
    })
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
    checkAndToastMock.mockReturnValue(true)
    const { getByText, getByLabelText } = render(
      <CreateAudit {...routeProps} />
    )

    fireEvent.change(getByLabelText('Give your new audit a unique name.'), {
      target: { value: 'Audit Name' },
    })
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

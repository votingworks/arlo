import React from 'react'
import { render, fireEvent, waitFor, screen } from '@testing-library/react'
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
  toastSpy.mockClear()
  historySpy.mockClear()
})

describe('CreateAudit', () => {
  it('renders correctly', async () => {
    apiMock.mockResolvedValueOnce(null)
    const { container } = render(
      <AuthDataProvider>
        <CreateAudit {...routeProps} />
      </AuthDataProvider>
    )
    await waitFor(() => expect(apiMock).toBeCalledTimes(1))
    expect(container).toMatchSnapshot()
  })

  it.skip('calls the /election/new endpoint for nonauthenticated user', async () => {
    // we have moved the unauthenticated functionality for creating an audit to CreateSingleJurisdictionAudit
    apiMock.mockResolvedValueOnce(null).mockResolvedValue({ electionId: '1' })
    const { getByText, getByLabelText } = render(
      <AuthDataProvider>
        <CreateAudit {...routeProps} />
      </AuthDataProvider>
    )

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
    })

    fireEvent.change(getByLabelText('Give your new audit a unique name.'), {
      target: { value: 'Audit Name' },
    })
    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toHaveBeenNthCalledWith(2, '/election/new', {
        method: 'POST',
        body: JSON.stringify({
          auditName: 'Audit Name',
          auditType: 'BALLOT_POLLING',
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
    apiMock
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({ electionId: '1' })
    const { getByText } = render(
      <AuthDataProvider>
        <CreateAudit {...routeProps} />
      </AuthDataProvider>
    )
    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
    })

    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await waitFor(() => {
      expect(getByText('Required')).toBeTruthy()
      expect(apiMock).toBeCalledTimes(1)
    })
  })

  it('calls the /election/new endpoint for authenticated user', async () => {
    apiMock
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({ electionId: '1' })
    const { getByText, queryByLabelText } = render(
      <AuthDataProvider>
        <CreateAudit {...routeProps} />
      </AuthDataProvider>
    )

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock).toHaveBeenNthCalledWith(1, '/me')
    })
    const auditName = queryByLabelText('Give your new audit a unique name.')
    await waitFor(() => expect(auditName).toBeTruthy())
    fireEvent.change(auditName!, {
      target: { value: 'Audit Name' },
    })
    fireEvent.click(getByText('Create a New Audit'), { bubbles: true })

    await waitFor(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(apiMock).toHaveBeenNthCalledWith(2, '/election/new', {
        method: 'POST',
        body: JSON.stringify({
          organizationId: 'org-id',
          auditName: 'Audit Name',
          auditType: 'BALLOT_POLLING',
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

  it.skip('lists associated elections for authenticated AA user', async () => {
    // TODO this is failing now
    apiMock.mockResolvedValue({
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
              auditName: 'Election One',
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
    })
    const { container } = render(
      <Router>
        <AuthDataProvider>
          <CreateAudit {...routeProps} />
        </AuthDataProvider>
      </Router>
    )

    await waitFor(() => expect(apiMock).toBeCalledTimes(1))
    expect(apiMock).toHaveBeenNthCalledWith(1, '/me')
    await screen.findByText('Election Four') // tests that it's actually listing them
    expect(container).toMatchSnapshot()
  })

  it.skip('lists associated elections for authenticated JA user', async () => {
    // TODO this is failing now
    apiMock.mockResolvedValue({
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
    })
    const { container } = render(
      <Router>
        <AuthDataProvider>
          <CreateAudit {...routeProps} />
        </AuthDataProvider>
      </Router>
    )

    await waitFor(() => expect(apiMock).toBeCalledTimes(1))
    expect(apiMock).toHaveBeenNthCalledWith(1, '/me')
    await screen.findByText('Election One') // tests that it's actually listing them
    expect(container).toMatchSnapshot()
  })
})

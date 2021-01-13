import React from 'react'
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastContainer } from 'react-toastify'
import { withMockFetch, renderWithRouter } from '../testUtilities'
import SupportTools from './SupportTools'
import AuthDataProvider from '../UserContext'
import { supportApiCalls } from '../MultiJurisdictionAudit/_mocks'

const apiCalls = {
  getOrganizations: {
    url: '/api/support/organizations',
    response: [
      { id: 'organization-id-1', name: 'Organization 1' },
      { id: 'organization-id-2', name: 'Organization 2' },
    ],
  },
  postOrganization: {
    url: '/api/support/organizations',
    options: {
      method: 'POST',
      body: JSON.stringify({
        name: 'New Organization',
      }),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  },
  getOrganization: {
    url: '/api/support/organizations/organization-id-1',
    response: {
      id: 'organization-id-1',
      name: 'Organization 1',
      elections: [
        {
          id: 'election-id-1',
          auditName: 'Audit 1',
          auditType: 'BALLOT_POLLING',
        },
        {
          id: 'election-id-2',
          auditName: 'Audit 2',
          auditType: 'BALLOT_COMPARISON',
        },
      ],
      auditAdmins: [
        { email: 'audit-admin-1@example.org' },
        { email: 'audit-admin-2@example.org' },
      ],
    },
  },
  getElection: {
    url: '/api/support/elections/election-id-1',
    response: {
      id: 'election-id-1',
      auditName: 'Audit 1',
      auditType: 'BALLOT_POLLING',
      jurisdictions: [
        {
          id: 'jurisdiction-id-1',
          name: 'Jurisdiction 1',
          jurisdictionAdmins: [
            { email: 'jurisdiction-admin-1@example.org' },
            { email: 'jurisdiction-admin-2@example.org' },
          ],
        },
        {
          id: 'jurisdiction-id-2',
          name: 'Jurisdiction 2',
          jurisdictionAdmins: [{ email: 'jurisdiction-admin-3@example.org' }],
        },
      ],
    },
  },
  postAuditAdmin: {
    url: '/api/support/organizations/organization-id-1/audit-admins',
    options: {
      method: 'POST',
      body: JSON.stringify({
        email: 'audit-admin-3@example.org',
      }),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  },
}

const serverError = (apiCall: { url: string; options?: object }) => ({
  ...apiCall,
  response: {
    errors: [{ errorType: 'Server Error', message: 'something went wrong' }],
  },
  error: { status: 500, statusText: 'Server Error' },
})

const renderRoute = (route: string) =>
  renderWithRouter(
    <AuthDataProvider>
      <SupportTools />
      <ToastContainer />
    </AuthDataProvider>,
    { route }
  )

describe('Support Tools', () => {
  it('home screen shows a list of orgs', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations,
      apiCalls.getOrganization,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support')

      await screen.findByRole('heading', { name: 'Organizations' })

      screen.getByRole('button', { name: 'Organization 2' })
      userEvent.click(screen.getByRole('button', { name: 'Organization 1' }))

      await screen.findByRole('heading', { name: 'Organization 1' })
      expect(history.location.pathname).toEqual(
        '/support/orgs/organization-id-1'
      )
    })
  })

  it('home screen shows a form to create a new org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations,
      apiCalls.postOrganization,
      {
        ...apiCalls.getOrganizations,
        response: [
          ...apiCalls.getOrganizations.response,
          { id: 'new-organization-id', name: 'New Organization' },
        ],
      },
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')

      await screen.findByRole('heading', { name: 'Organizations' })

      userEvent.type(
        screen.getByPlaceholderText('New organization name'),
        'New Organization'
      )
      userEvent.click(
        screen.getByRole('button', { name: /Create Organization/ })
      )

      await screen.findByRole('button', { name: 'New Organization' })
    })
  })

  it('org screen shows a list of audits', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization,
      apiCalls.getElection,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      screen.getByRole('button', { name: 'Audit 2' })
      userEvent.click(screen.getByRole('button', { name: 'Audit 1' }))

      await screen.findByRole('heading', { name: 'Audit 1' })
      expect(history.location.pathname).toEqual('/support/audits/election-id-1')
    })
  })

  it('org screen shows a list of audit admins and a form to create a new audit admin', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization,
      apiCalls.postAuditAdmin,
      {
        ...apiCalls.getOrganization,
        response: {
          ...apiCalls.getOrganization.response,
          auditAdmins: [
            ...apiCalls.getOrganization.response.auditAdmins,
            { email: 'audit-admin-3@example.org' },
          ],
        },
      },
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      // List of admins with log in buttons
      screen.getByText('audit-admin-2@example.org')
      const logInAsButton = within(
        screen.getByText('audit-admin-1@example.org').closest('tr')!
      ).getByRole('button', { name: /Log in as/ })
      expect(logInAsButton).toHaveAttribute(
        'href',
        '/api/support/audit-admins/audit-admin-1@example.org/login'
      )

      // Create a new admin
      userEvent.type(
        screen.getByPlaceholderText('New admin email'),
        'audit-admin-3@example.org'
      )
      userEvent.click(
        screen.getByRole('button', { name: /Create Audit Admin/ })
      )

      expect(screen.getByPlaceholderText('New admin email')).toHaveTextContent(
        ''
      )
      await screen.findByText('audit-admin-3@example.org')
    })
  })

  it('audit screen shows a list of jurisdiction admins', async () => {
    const expectedCalls = [supportApiCalls.getUser, apiCalls.getElection]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/audits/election-id-1')

      await screen.findByRole('heading', { name: 'Audit 1' })
      screen.getByText('Ballot Polling')

      // List of jurisdictions
      screen.getByRole('heading', { name: 'Jurisdiction 2' })
      const jurisdiction1Container = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div')!

      // List of jurisdiction admins with log in buttons
      within(jurisdiction1Container).getByText(
        'jurisdiction-admin-2@example.org'
      )
      const logInAsButton = within(
        within(jurisdiction1Container)
          .getByText('jurisdiction-admin-1@example.org')
          .closest('tr')!
      ).getByRole('button', { name: /Log in as/ })
      expect(logInAsButton).toHaveAttribute(
        'href',
        '/api/support/jurisdiction-admins/jurisdiction-admin-1@example.org/login'
      )
    })
  })

  it('home screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(apiCalls.getOrganizations),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('home screen handles error on create org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations,
      serverError(apiCalls.postOrganization),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')

      await screen.findByRole('heading', { name: 'Organizations' })

      userEvent.type(
        screen.getByPlaceholderText('New organization name'),
        'New Organization'
      )
      userEvent.click(
        screen.getByRole('button', { name: /Create Organization/ })
      )

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('org screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(apiCalls.getOrganization),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('org screen handles error on create admin', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization,
      serverError(apiCalls.postAuditAdmin),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      // Create a new admin
      userEvent.type(
        screen.getByPlaceholderText('New admin email'),
        'audit-admin-3@example.org'
      )
      userEvent.click(
        screen.getByRole('button', { name: /Create Audit Admin/ })
      )

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('audit screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(apiCalls.getElection),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/audits/election-id-1')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })
})

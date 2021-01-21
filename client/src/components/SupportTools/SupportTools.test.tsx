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
        },
        {
          id: 'jurisdiction-id-2',
          name: 'Jurisdiction 2',
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
  deleteAuditBoards: {
    url: '/api/support/jurisdictions/jurisdiction-id-1/audit-boards',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  getJurisdiction: {
    url: '/api/support/jurisdictions/jurisdiction-id-1',
    response: {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      jurisdictionAdmins: [
        { email: 'jurisdiction-admin-1@example.org' },
        { email: 'jurisdiction-admin-2@example.org' },
      ],
      auditBoards: [
        {
          id: 'audit-board-id-1',
          name: 'Audit Board #1',
          signedOffAt: '2021-01-21T18:19:35.493+00:00',
        },
        { id: 'audit-board-id-2', name: 'Audit Board #2', signedOffAt: null },
      ],
    },
  },
  reopenAuditBoard: {
    url: '/api/support/audit-boards/audit-board-id-1/sign-off',
    options: { method: 'DELETE' },
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

  it('audit screen shows a list of jurisdictions', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getElection,
      apiCalls.getJurisdiction,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support/audits/election-id-1')

      await screen.findByRole('heading', { name: 'Audit 1' })
      screen.getByText('Ballot Polling')

      // List of jurisdictions
      screen.getByRole('button', { name: 'Jurisdiction 2' })
      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })
      expect(history.location.pathname).toEqual(
        '/support/jurisdictions/jurisdiction-id-1'
      )
    })
  })

  it('jurisdiction screen shows a list of audit boards', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction,
      apiCalls.reopenAuditBoard,
      {
        ...apiCalls.getJurisdiction,
        response: {
          ...apiCalls.getJurisdiction.response,
          auditBoards: [
            {
              id: 'audit-board-id-1',
              name: 'Audit Board #1',
              signedOffAt: null,
            },
            {
              id: 'audit-board-id-2',
              name: 'Audit Board #2',
              signedOffAt: null,
            },
          ],
        },
      },
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      // List of audit boards with reopen buttons
      screen.getByRole('heading', { name: 'Current Round Audit Boards' })
      const reopenButton1 = within(
        screen.getByText('Audit Board #1').closest('tr')!
      ).getByRole('button', { name: 'Reopen' })
      const reopenButton2 = within(
        screen.getByText('Audit Board #2').closest('tr')!
      ).getByRole('button', { name: 'Reopen' })
      // If audit board has not signed off, button is disabled
      expect(reopenButton2).toBeDisabled()

      // Click reopen button
      userEvent.click(reopenButton1)

      // Confirm dialog should open
      const dialog = (await screen.findByRole('heading', {
        name: /Confirm/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to reopen Audit Board #1?'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Reopen' }))

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('Reopened Audit Board #1')

      expect(
        within(screen.getByText('Audit Board #1').closest('tr')!).getByRole(
          'button',
          { name: 'Reopen' }
        )
      ).toBeDisabled()
    })
  })

  it('jurisdiction screen shows a list of jurisdiction admins', async () => {
    const expectedCalls = [supportApiCalls.getUser, apiCalls.getJurisdiction]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      // List of jurisdiction admins with log in buttons
      screen.getByRole('heading', { name: 'Jurisdiction Admins' })
      screen.getByText('jurisdiction-admin-2@example.org')
      const logInAsButton = within(
        screen.getByText('jurisdiction-admin-1@example.org').closest('tr')!
      ).getByRole('button', { name: /Log in as/ })
      expect(logInAsButton).toHaveAttribute(
        'href',
        '/api/support/jurisdiction-admins/jurisdiction-admin-1@example.org/login'
      )
    })
  })

  it('jurisdiction screen shows a button to clear audit boards', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction,
      apiCalls.deleteAuditBoards,
      {
        ...apiCalls.getJurisdiction,
        response: {
          ...apiCalls.getJurisdiction.response,
          auditBoards: [],
        },
      },
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      // Click clear audit boards button
      userEvent.click(
        screen.getByRole('button', {
          name: /Clear audit boards/,
        })
      )

      // Confirm dialog should open
      const dialog = screen
        .getByRole('heading', { name: /Confirm/ })
        .closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to clear the audit boards for Jurisdiction 1?'
      )
      userEvent.click(
        within(dialog).getByRole('button', { name: /Clear audit boards/ })
      )

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('Cleared audit boards for Jurisdiction 1')

      screen.getByText("The jurisdiction hasn't created audit boards yet.")
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

  it('jurisdiction screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(apiCalls.getJurisdiction),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('jurisdiction screen handles error on clear audit boards', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction,
      serverError(apiCalls.deleteAuditBoards),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      // Click clear audit boards button
      userEvent.click(
        screen.getByRole('button', {
          name: /Clear audit boards/,
        })
      )

      // Confirm dialog should open
      const dialog = screen
        .getByRole('heading', { name: /Confirm/ })
        .closest('.bp3-dialog')! as HTMLElement
      userEvent.click(
        within(dialog).getByRole('button', { name: /Clear audit boards/ })
      )

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('jurisdiction screen handles error on reopen audit board', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction,
      serverError(apiCalls.reopenAuditBoard),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      // Click reopen button
      const reopenButton1 = within(
        screen.getByText('Audit Board #1').closest('tr')!
      ).getByRole('button', { name: 'Reopen' })
      userEvent.click(reopenButton1)

      // Confirm dialog should open
      const dialog = (await screen.findByRole('heading', {
        name: /Confirm/,
      })).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: 'Reopen' }))

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })
})

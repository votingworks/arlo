import React from 'react'
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastContainer } from 'react-toastify'
import { withMockFetch, renderWithRouter } from '../testUtilities'
import SupportTools from './SupportTools'
import AuthDataProvider from '../UserContext'
import { supportApiCalls } from '../MultiJurisdictionAudit/_mocks'
import {
  IOrganizationBase,
  IOrganization,
  IElectionBase,
  IElection,
  IJurisdictionBase,
  IJurisdiction,
} from './support-api'

const mockOrganizationBase: IOrganizationBase = {
  id: 'organization-id-1',
  name: 'Organization 1',
}

const mockElectionBase: IElectionBase = {
  id: 'election-id-1',
  auditName: 'Audit 1',
  auditType: 'BALLOT_POLLING',
  online: true,
}

const mockJurisdictionBase: IJurisdictionBase = {
  id: 'jurisdiction-id-1',
  name: 'Jurisdiction 1',
}

const mockOrganization: IOrganization = {
  ...mockOrganizationBase,
  elections: [
    mockElectionBase,
    {
      id: 'election-id-2',
      auditName: 'Audit 2',
      auditType: 'BALLOT_COMPARISON',
      online: false,
    },
  ],
  auditAdmins: [
    { email: 'audit-admin-1@example.org' },
    { email: 'audit-admin-2@example.org' },
  ],
}

const mockElection: IElection = {
  ...mockElectionBase,
  jurisdictions: [
    mockJurisdictionBase,
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
    },
  ],
}

const mockJurisdiction: IJurisdiction = {
  ...mockJurisdictionBase,
  election: mockElectionBase,
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
  recordedResultsAt: null,
}

const apiCalls = {
  getOrganizations: (response: IOrganizationBase[]) => ({
    url: '/api/support/organizations',
    response,
  }),
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
  getOrganization: (response: IOrganization) => ({
    url: '/api/support/organizations/organization-id-1',
    response,
  }),
  getElection: (response: IElection) => ({
    url: '/api/support/elections/election-id-1',
    response,
  }),
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
  getJurisdiction: (response: IJurisdiction) => ({
    url: '/api/support/jurisdictions/jurisdiction-id-1',
    response,
  }),
  reopenAuditBoard: {
    url: '/api/support/audit-boards/audit-board-id-1/sign-off',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  deleteOfflineResults: {
    url: '/api/support/jurisdictions/jurisdiction-id-1/results',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
}

const serverError = (
  name: string,
  apiCall: { url: string; options?: object }
) => ({
  ...apiCall,
  response: {
    errors: [
      { errorType: 'Server Error', message: `something went wrong: ${name}` },
    ],
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
      apiCalls.getOrganizations([
        mockOrganizationBase,
        { id: 'organization-id-2', name: 'Organization 2' },
      ]),
      apiCalls.getOrganization(mockOrganization),
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

  it('home screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError('getOrganizations', apiCalls.getOrganizations([])),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong: getOrganizations')
    })
  })

  it('home screen shows a form to create a new org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations([]),
      apiCalls.postOrganization,
      apiCalls.getOrganizations([
        { id: 'new-organization-id', name: 'New Organization' },
      ]),
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

  it('home screen handles error on create org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations([]),
      serverError('postOrganization', apiCalls.postOrganization),
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
      expect(toast).toHaveTextContent('something went wrong: postOrganization')
    })
  })

  it('org screen shows a list of audits', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      apiCalls.getElection(mockElection),
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

  it('org screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(
        'getOrganization',
        apiCalls.getOrganization(mockOrganization)
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong')
    })
  })

  it('org screen shows a list of audit admins and a form to create a new audit admin', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      apiCalls.postAuditAdmin,
      apiCalls.getOrganization({
        ...mockOrganization,
        auditAdmins: [
          ...mockOrganization.auditAdmins,
          { email: 'audit-admin-3@example.org' },
        ],
      }),
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

  it('org screen handles error on create admin', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      serverError('postAuditAdmin', apiCalls.postAuditAdmin),
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
      expect(toast).toHaveTextContent('something went wrong: postAuditAdmin')
    })
  })

  it('audit screen shows a list of jurisdictions', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getElection(mockElection),
      apiCalls.getJurisdiction(mockJurisdiction),
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

  it('audit screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError('getElection', apiCalls.getElection(mockElection)),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/audits/election-id-1')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong: getElection')
    })
  })

  it('jurisdiction screen shows a list of audit boards with buttons to reopen them', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
      apiCalls.reopenAuditBoard,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
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
      }),
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

  it('jurisdiction screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(
        'getJurisdiction',
        apiCalls.getJurisdiction(mockJurisdiction)
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong: getJurisdiction')
    })
  })

  it('jurisdiction screen handles error on reopen audit board', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
      serverError('reopenAuditBoard', apiCalls.reopenAuditBoard),
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
      expect(toast).toHaveTextContent('something went wrong: reopenAuditBoard')
    })
  })

  it('jurisdiction screen shows a list of jurisdiction admins', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
    ]
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
      apiCalls.getJurisdiction(mockJurisdiction),
      apiCalls.deleteAuditBoards,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
        auditBoards: [],
      }),
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

  it('jurisdiction screen handles error on clear audit boards', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
      serverError('deleteAuditBoards', apiCalls.deleteAuditBoards),
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
      expect(toast).toHaveTextContent('something went wrong: deleteAuditBoards')
    })
  })

  it('jurisdiction screen shows offline results and a button to clear them', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
        election: { ...mockElection, online: false },
        recordedResultsAt: '2021-06-23T18:51:56.759+00:00',
      }),
      apiCalls.deleteOfflineResults,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
        election: { ...mockElection, online: false },
        recordedResultsAt: null,
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      screen.getByRole('heading', { name: 'Offline Results' })
      screen.getByText('Results recorded at 6/23/2021, 6:51:56 PM.')

      userEvent.click(
        screen.getByRole('button', {
          name: /Clear results/,
        })
      )

      const dialog = screen
        .getByRole('heading', { name: /Confirm/ })
        .closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to clear results for Jurisdiction 1?'
      )
      userEvent.click(
        within(dialog).getByRole('button', { name: /Clear results/ })
      )

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('Cleared results for Jurisdiction 1')

      screen.getByText('No results recorded yet.')
    })
  })

  it('jurisdiction screen handles error on clear results', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
        election: { ...mockElection, online: false },
        recordedResultsAt: '2021-06-23T18:51:56.759+00:00',
      }),
      serverError('deleteOfflineResults', apiCalls.deleteOfflineResults),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      userEvent.click(
        screen.getByRole('button', {
          name: /Clear results/,
        })
      )

      const dialog = screen
        .getByRole('heading', { name: /Confirm/ })
        .closest('.bp3-dialog')! as HTMLElement
      userEvent.click(
        within(dialog).getByRole('button', { name: /Clear results/ })
      )

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent(
        'something went wrong: deleteOfflineResults'
      )
    })
  })
})

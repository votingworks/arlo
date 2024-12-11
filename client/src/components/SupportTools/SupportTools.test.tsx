import React from 'react'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastContainer } from 'react-toastify'
import { QueryClientProvider } from 'react-query'
import {
  withMockFetch,
  renderWithRouter,
  serverError,
  findAndCloseToast,
  createQueryClient,
} from '../testUtilities'
import SupportTools from './SupportTools'
import AuthDataProvider from '../UserContext'
import { supportApiCalls } from '../_mocks'
import {
  IOrganizationBase,
  IElection,
  IJurisdictionBase,
  IJurisdiction,
  IRound,
  IBatch,
  ICombinedBatch,
  IElectionForSupport,
  IOrganizationForSupport,
  IElectionBase,
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
  deletedAt: null,
}

const mockElectionForSupport: IElectionForSupport = {
  ...mockElectionBase,
  organization: mockOrganizationBase,
  createdAt: '2022-02-08T21:03:35.487Z',
  currentRound: null,
}

const mockJurisdictionBase: IJurisdictionBase = {
  id: 'jurisdiction-id-1',
  name: 'Jurisdiction 1',
}

const mockOrganization: IOrganizationForSupport = {
  ...mockOrganizationBase,
  defaultState: null,
  elections: [
    mockElectionForSupport,
    {
      id: 'election-id-2',
      auditName: 'Audit 2',
      auditType: 'BALLOT_COMPARISON',
      online: false,
      deletedAt: null,
      createdAt: '2022-02-08T21:03:35.487Z',
      organization: mockOrganizationBase,
      currentRound: {
        id: 'round-2',
        endedAt: null,
        roundNum: 1,
      },
    },
    {
      id: 'election-id-3',
      auditName: 'Audit 3',
      auditType: 'BATCH_COMPARISON',
      online: false,
      deletedAt: '2022-03-08T21:03:35.487Z',
      createdAt: '2022-02-08T21:03:35.487Z',
      organization: mockOrganizationBase,
      currentRound: {
        id: 'round-3',
        endedAt: '2022-03-07T21:03:35.487Z',
        roundNum: 1,
      },
    },
    {
      id: 'election-id-3',
      auditName: 'Audit 4',
      auditType: 'BATCH_COMPARISON',
      online: false,
      deletedAt: null,
      createdAt: '2022-02-08T21:03:35.487Z',
      organization: mockOrganizationBase,
      currentRound: {
        id: 'round-3',
        endedAt: '2022-03-07T21:03:35.487Z',
        roundNum: 1,
      },
    },
  ],
  auditAdmins: [
    { id: 'audit-admin-1-id', email: 'audit-admin-1@example.org' },
    { id: 'audit-admin-2-id', email: 'audit-admin-2@example.org' },
  ],
}

const mockElection: IElection = {
  ...mockElectionForSupport,
  jurisdictions: [
    mockJurisdictionBase,
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
    },
  ],
  rounds: [{ id: 'round-1', endedAt: null, roundNum: 1 }],
}

const mockJurisdiction: IJurisdiction = {
  ...mockJurisdictionBase,
  organization: mockOrganizationBase,
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

const mockJurisdictionBatches: {
  batches: IBatch[]
  combinedBatches: ICombinedBatch[]
} = {
  batches: [
    { id: 'batch-id-1', name: 'Batch 1' },
    { id: 'batch-id-2', name: 'Batch 2' },
    { id: 'batch-id-3', name: 'Batch 3' },
    { id: 'batch-id-4', name: 'Batch 4' },
  ],
  combinedBatches: [],
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
  getOrganization: (response: IOrganizationForSupport) => ({
    url: '/api/support/organizations/organization-id-1',
    response,
  }),
  updateOrganization: (body: {
    name: string
    defaultState: string | null
  }) => ({
    url: '/api/support/organizations/organization-id-1',
    options: {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  }),
  deleteOrganization: {
    url: '/api/support/organizations/organization-id-1',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  deleteElection: {
    url: '/api/support/elections/election-id-3',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  getActiveElections: (response: IElectionForSupport[]) => ({
    url: '/api/support/elections/active',
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
  removeAuditAdmin: {
    url:
      '/api/support/organizations/organization-id-1/audit-admins/audit-admin-1-id',
    options: { method: 'DELETE' },
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
  getJurisdictionBatches: (response: {
    batches: IBatch[]
    combinedBatches: ICombinedBatch[]
  }) => ({
    url: '/api/support/jurisdictions/jurisdiction-id-1/batches',
    response,
  }),
  postCombinedBatch: {
    url: '/api/support/jurisdictions/jurisdiction-id-1/combined-batches',
    options: {
      method: 'POST',
      body: JSON.stringify({
        name: 'Combined Batch 1',
        subBatchIds: ['batch-id-1', 'batch-id-2'],
      }),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  },
  deleteCombinedBatch: {
    url:
      '/api/support/jurisdictions/jurisdiction-id-1/combined-batches/Combined Batch 1',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  deleteOfflineResults: {
    url: '/api/support/jurisdictions/jurisdiction-id-1/results',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  undoRoundStart: {
    url: '/api/support/rounds/round-2',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  reopenCurrentRound: {
    url: '/api/support/elections/election-id-1/reopen-current-round',
    options: { method: 'PATCH' },
    response: { status: 'ok' },
  },
}

const renderRoute = (route: string) =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <AuthDataProvider>
        <SupportTools />
        <ToastContainer />
      </AuthDataProvider>
    </QueryClientProvider>,
    { route }
  )

beforeAll(() => {
  // eslint-disable-next-line no-console
  console.error = jest.fn()
})

describe('Support Tools', () => {
  it('home screen shows active audits', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations([]),
      apiCalls.getActiveElections([
        mockElectionForSupport,
        {
          ...mockElectionForSupport,
          id: 'election-id-2',
          auditName: 'Audit 2',
          organization: mockOrganizationBase,
          currentRound: { id: 'round-1', endedAt: null, roundNum: 1 },
        },
      ]),
      apiCalls.getElection(mockElection),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support')

      await screen.findByRole('heading', { name: 'Active Audits' })
      screen.getByRole('link', {
        name: 'Organization 1 Audit 2 Round 1 In Progress',
      })
      userEvent.click(
        screen.getByRole('link', { name: 'Organization 1 Audit 1 Not Started' })
      )
      await screen.findByRole('heading', { name: 'Audit 1' })
      expect(history.location.pathname).toEqual('/support/audits/election-id-1')
    })
  })

  it('home screen shows a list of orgs', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations([
        mockOrganizationBase,
        { id: 'organization-id-2', name: 'Organization 2' },
      ]),
      apiCalls.getActiveElections([]),
      apiCalls.getOrganization(mockOrganization),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support')

      await screen.findByRole('heading', { name: 'Organizations' })
      screen.getByRole('link', { name: 'Organization 2' })
      userEvent.click(screen.getByRole('link', { name: 'Organization 1' }))

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
      apiCalls.getActiveElections([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')
      await findAndCloseToast('something went wrong: getOrganizations')
    })
  })

  it('home screen shows a form to create a new org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations([]),
      apiCalls.getActiveElections([]),
      apiCalls.postOrganization,
      apiCalls.getOrganizations([
        { id: 'new-organization-id', name: 'New Organization' },
      ]),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')

      await screen.findByRole('heading', { name: 'Organizations' })

      userEvent.type(
        screen.getByPlaceholderText('Organization name'),
        'New Organization'
      )
      userEvent.click(screen.getByRole('button', { name: /Create Org/ }))

      await screen.findByRole('link', { name: 'New Organization' })
    })
  })

  it('home screen handles error on create org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganizations([]),
      apiCalls.getActiveElections([]),
      serverError('postOrganization', apiCalls.postOrganization),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support')

      await screen.findByRole('heading', { name: 'Organizations' })

      userEvent.type(
        screen.getByPlaceholderText('Organization name'),
        'New Organization'
      )
      userEvent.click(screen.getByRole('button', { name: /Create Org/ }))

      await findAndCloseToast('something went wrong: postOrganization')
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

      screen.getByRole('heading', { name: 'Audits' })
      screen.getByRole('link', { name: 'Audit 2 Round 1 In Progress' })
      screen.getByRole('link', { name: 'Audit 4 Completed' })
      screen.getByRole('link', { name: 'Audit 1 Not Started' })

      screen.getByRole('heading', { name: 'Deleted Audits' })
      screen.getByRole('row', { name: /Audit 3/ })

      userEvent.click(screen.getByRole('link', { name: 'Audit 1 Not Started' }))
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
      await findAndCloseToast('something went wrong: getOrganization')
    })
  })

  it('org screen has a button to permanently delete an audit', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      apiCalls.deleteElection,
      apiCalls.getOrganization({
        ...mockOrganization,
        elections: mockOrganization.elections.filter(
          e => e.auditName !== 'Audit 3'
        ),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      const auditRow = screen.getByRole('row', { name: /Audit 3/ })
      userEvent.click(
        within(auditRow).getByRole('button', {
          name: /Permanently Delete/,
        })
      )

      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to permanently delete Audit 3?'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('Deleted Audit 3')
      expect(screen.queryByText('Audit 3')).not.toBeInTheDocument()
    })
  })

  it('org screen handles error on delete audit', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      serverError('deleteElection', apiCalls.deleteElection),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      const auditRow = screen.getByRole('row', { name: /Audit 3/ })
      userEvent.click(
        within(auditRow).getByRole('button', {
          name: /Permanently Delete/,
        })
      )
      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))

      await findAndCloseToast('something went wrong: deleteElection')
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
          { id: 'audit-admin-3-id', email: 'audit-admin-3@example.org' },
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

      await findAndCloseToast('something went wrong: postAuditAdmin')
    })
  })

  it('org screen has a button to remove audit admin', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      apiCalls.removeAuditAdmin,
      apiCalls.getOrganization({
        ...mockOrganization,
        auditAdmins: mockOrganization.auditAdmins.slice(1),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      // Remove an admin
      userEvent.click(
        within(
          screen.getByText('audit-admin-1@example.org').closest('tr')!
        ).getByRole('button', { name: /Remove/ })
      )

      // Confirm dialog should open
      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to remove audit admin audit-admin-1@example.org from organization Organization 1?'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Remove' }))

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent(
        'Removed audit admin audit-admin-1@example.org'
      )
      expect(
        screen.queryByText('audit-admin-1@example.org')
      ).not.toBeInTheDocument()
    })
  })

  it('org screen handles error on remove audit admin', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      serverError('removeAuditAdmin', apiCalls.removeAuditAdmin),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })
      userEvent.click(
        within(
          screen.getByText('audit-admin-1@example.org').closest('tr')!
        ).getByRole('button', { name: /Remove/ })
      )

      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: 'Remove' }))

      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong: removeAuditAdmin')
      expect(dialog).toBeInTheDocument()
    })
  })

  it('org screen has a button to edit the org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      apiCalls.updateOrganization({ name: 'New Org Name', defaultState: null }),
      apiCalls.getOrganization({ ...mockOrganization, name: 'New Org Name' }),
      apiCalls.updateOrganization({ name: 'New Org Name', defaultState: 'CA' }),
      apiCalls.getOrganization({
        ...mockOrganization,
        name: 'New Org Name',
        defaultState: 'CA',
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })
      screen.getByText('Default State: None')

      userEvent.click(screen.getByRole('button', { name: /Edit/ }))

      let dialog = (
        await screen.findByRole('heading', {
          name: /Edit Organization/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      const nameInput = within(dialog).getByLabelText('Name:')
      userEvent.clear(nameInput)
      userEvent.type(nameInput, 'New Org Name')
      userEvent.click(within(dialog).getByRole('button', { name: 'Submit' }))

      await screen.findByRole('heading', { name: 'New Org Name' })
      screen.getByText('Default State: None')

      userEvent.click(screen.getByRole('button', { name: /Edit/ }))
      dialog = (
        await screen.findByRole('heading', {
          name: /Edit Organization/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      userEvent.selectOptions(
        within(dialog).getByLabelText('Default State:'),
        'California'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Submit' }))

      await screen.findByText('Default State: California')
      screen.getByRole('heading', { name: 'New Org Name' })
    })
  })

  it('org screen handles errors on edit', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      serverError(
        'renameOrganization',
        apiCalls.updateOrganization({
          name: 'New Org Name',
          defaultState: null,
        })
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      userEvent.click(screen.getByRole('button', { name: /Edit/ }))

      // Confirm dialog should open
      const dialog = (
        await screen.findByRole('heading', {
          name: /Edit Organization/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      const nameInput = within(dialog).getByLabelText('Name:')
      userEvent.clear(nameInput)
      userEvent.type(nameInput, 'New Org Name')
      userEvent.click(within(dialog).getByRole('button', { name: 'Submit' }))

      await findAndCloseToast('something went wrong: renameOrganization')
      expect(dialog).toBeInTheDocument()
    })
  })

  it('org screen has a button to delete the org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      apiCalls.deleteOrganization,
      apiCalls.getOrganizations([]),
      apiCalls.getActiveElections([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      userEvent.click(screen.getByRole('button', { name: 'delete Delete' }))

      // Confirm dialog should open
      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to delete organization Organization 1?'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))

      await findAndCloseToast('Deleted organization Organization 1')

      await screen.findByRole('heading', { name: 'Organizations' })
      expect(history.location.pathname).toEqual('/support')
      expect(
        screen.queryByRole('button', { name: 'Organization 1' })
      ).not.toBeInTheDocument()
    })
  })

  it('org screen handles error on delete org', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getOrganization(mockOrganization),
      serverError('deleteOrganization', apiCalls.deleteOrganization),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support/orgs/organization-id-1')

      await screen.findByRole('heading', { name: 'Organization 1' })

      userEvent.click(screen.getByRole('button', { name: 'delete Delete' }))

      // Confirm dialog should open
      const dialog = (
        await screen.findByRole('heading', {
          name: /Confirm/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to delete organization Organization 1?'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))

      await findAndCloseToast('something went wrong: deleteOrganization')
      expect(history.location.pathname).toEqual(
        '/support/orgs/organization-id-1'
      )
    })
  })

  it('audit screen shows login button and list of jurisdictions', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getElection(mockElection),
      apiCalls.getJurisdiction(mockJurisdiction),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderRoute('/support/audits/election-id-1')

      await screen.findByRole('heading', { name: 'Audit 1' })

      const organizationLink = screen.getByRole('link', {
        name: /Organization 1/,
      })
      expect(organizationLink).toHaveAttribute(
        'href',
        '/support/orgs/organization-id-1'
      )

      const adminLoginButton = screen.getByRole('button', {
        name: /Log in as audit admin/,
      })
      expect(adminLoginButton).toHaveAttribute(
        'href',
        '/api/support/elections/election-id-1/login'
      )

      screen.getByText('Ballot Polling')

      const jurisdictionLink = screen.getByRole('link', {
        name: /Jurisdiction 1/,
      })
      const jurisdictionLoginButton = within(
        jurisdictionLink
      ).getByRole('button', { name: /Log in/ })
      expect(jurisdictionLoginButton).toHaveAttribute(
        'href',
        '/api/support/jurisdictions/jurisdiction-id-1/login'
      )
      screen.getByRole('link', { name: /Jurisdiction 2/ })
      userEvent.click(jurisdictionLink)

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })
      expect(history.location.pathname).toEqual(
        '/support/jurisdictions/jurisdiction-id-1'
      )
    })
  })

  const roundSummaryTestCases: {
    rounds: IRound[]
    expectedRoundsTableHead: string[]
    expectedRoundsTableBody: {
      round: string
      status: string
      action?: string
    }[]
  }[] = [
    {
      rounds: [],
      expectedRoundsTableHead: ['Round', 'Status'],
      expectedRoundsTableBody: [{ round: 'Round 1', status: 'Not started' }],
    },
    {
      rounds: [{ id: 'round-1', endedAt: null, roundNum: 1 }],
      expectedRoundsTableHead: ['Round', 'Status', 'Actions'],
      expectedRoundsTableBody: [
        { round: 'Round 1', status: 'In progress', action: 'Undo Start' },
      ],
    },
    {
      rounds: [
        { id: 'round-1', endedAt: 'some-timestamp', roundNum: 1 },
        { id: 'round-2', endedAt: null, roundNum: 2 },
      ],
      expectedRoundsTableHead: ['Round', 'Status', 'Actions'],
      expectedRoundsTableBody: [
        { round: 'Round 1', status: 'Completed' },
        { round: 'Round 2', status: 'In progress', action: 'Undo Start' },
      ],
    },
    {
      rounds: [{ id: 'round-1', endedAt: 'some-timestamp', roundNum: 1 }],
      expectedRoundsTableHead: ['Round', 'Status', 'Actions'],
      expectedRoundsTableBody: [
        { round: 'Round 1', status: 'Completed', action: 'Reopen' },
      ],
    },
  ]
  it.each(roundSummaryTestCases)(
    'audit screen shows expected round summary',
    async ({ rounds, expectedRoundsTableHead, expectedRoundsTableBody }) => {
      const expectedCalls = [
        supportApiCalls.getUser,
        apiCalls.getElection({ ...mockElection, rounds }),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderRoute('/support/audits/election-id-1')

        await screen.findByRole('heading', { name: 'Audit 1' })
        expectedRoundsTableHead.forEach(header => {
          screen.getByRole('columnheader', { name: header })
        })
        expectedRoundsTableBody.forEach(row => {
          screen.getByRole('row', {
            name: row.action
              ? `${row.round} ${row.status} ${row.action}`
              : `${row.round} ${row.status}`,
          })
          screen.getByRole('cell', { name: row.round })
          screen.getByRole('cell', { name: row.status })
          if (row.action) {
            screen.getByRole('cell', { name: row.action })
            screen.getByRole('button', { name: row.action })
          }
        })
      })
    }
  )

  it('audit screen supports undoing round starts and reopening rounds', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getElection({
        ...mockElection,
        rounds: [
          { id: 'round-1', endedAt: 'some-timestamp', roundNum: 1 },
          { id: 'round-2', endedAt: null, roundNum: 2 },
        ],
      }),
      apiCalls.undoRoundStart,
      apiCalls.getElection({
        ...mockElection,
        rounds: [{ id: 'round-1', endedAt: 'some-timestamp', roundNum: 1 }],
      }),
      apiCalls.reopenCurrentRound,
      apiCalls.getElection({
        ...mockElection,
        rounds: [{ id: 'round-1', endedAt: null, roundNum: 1 }],
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/audits/election-id-1')

      await screen.findByRole('heading', { name: 'Audit 1' })

      userEvent.click(screen.getByText('Undo Start'))
      let confirmDialog = screen
        .getByRole('heading', { name: 'Confirm' })
        .closest('.bp3-dialog')! as HTMLElement
      within(confirmDialog).getByText(
        'Are you sure you want to undo the start of round 2?'
      )
      userEvent.click(
        within(confirmDialog).getByRole('button', { name: 'Undo Start' })
      )
      await waitFor(() => expect(confirmDialog).not.toBeInTheDocument())

      userEvent.click(screen.getByText('Reopen'))
      confirmDialog = screen
        .getByRole('heading', { name: 'Confirm' })
        .closest('.bp3-dialog')! as HTMLElement
      within(confirmDialog).getByText(
        'Are you sure you want to reopen round 1?'
      )
      userEvent.click(
        within(confirmDialog).getByRole('button', { name: 'Reopen' })
      )
      await waitFor(() => expect(confirmDialog).not.toBeInTheDocument())
    })
  })

  it('audit screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError('getElection', apiCalls.getElection(mockElection)),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/audits/election-id-1')
      await findAndCloseToast('something went wrong: getElection')
    })
  })

  it('jurisdiction screen shows a list of audit boards', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })
      screen.getByRole('heading', { name: 'Current Round Audit Boards' })
      screen.getByText('Audit Board #1')
      screen.getByText('Audit Board #2')

      const organizationLink = screen.getByRole('link', {
        name: /Organization 1/,
      })
      expect(organizationLink).toHaveAttribute(
        'href',
        '/support/orgs/organization-id-1'
      )

      const auditLink = screen.getByRole('link', { name: /Audit 1/ })
      expect(auditLink).toHaveAttribute('href', '/support/audits/election-id-1')
    })
  })

  it("jurisdiction screen doesn't shows a list of audit boards for batch comparison audits", async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
        election: { ...mockElection, auditType: 'BATCH_COMPARISON' },
      }),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })
      expect(
        screen.queryByRole('heading', { name: 'Current Round Audit Boards' })
      ).not.toBeInTheDocument()
    })
  })

  it('jurisdiction screen handles error', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      serverError(
        'getJurisdiction',
        apiCalls.getJurisdiction(mockJurisdiction)
      ),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')
      await findAndCloseToast('something went wrong: getJurisdiction')
    })
  })

  it('jurisdiction screen shows a list of jurisdiction admins', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
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
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
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

      await findAndCloseToast('Cleared audit boards for Jurisdiction 1')

      screen.getByText("The jurisdiction hasn't created audit boards yet.")
    })
  })

  it('jurisdiction screen handles error on clear audit boards', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction(mockJurisdiction),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
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

      await findAndCloseToast('something went wrong: deleteAuditBoards')
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
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
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

      await findAndCloseToast('Cleared results for Jurisdiction 1')

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
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
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

      await findAndCloseToast('something went wrong: deleteOfflineResults')
    })
  })

  it('jurisdiction screen shows form for combining batches in batch comparison audits', async () => {
    const expectedCalls = [
      supportApiCalls.getUser,
      apiCalls.getJurisdiction({
        ...mockJurisdiction,
        election: { ...mockElection, auditType: 'BATCH_COMPARISON' },
      }),
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
      apiCalls.postCombinedBatch,
      apiCalls.getJurisdictionBatches({
        ...mockJurisdictionBatches,
        combinedBatches: [
          {
            name: 'Combined Batch 1',
            subBatches: [
              {
                id: 'batch-id-1',
                name: 'Batch 1',
              },
              {
                id: 'batch-id-2',
                name: 'Batch 2',
              },
            ],
          },
        ],
      }),
      apiCalls.deleteCombinedBatch,
      apiCalls.getJurisdictionBatches(mockJurisdictionBatches),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderRoute('/support/jurisdictions/jurisdiction-id-1')

      await screen.findByRole('heading', { name: 'Jurisdiction 1' })

      userEvent.type(
        screen.getByLabelText('Combined Batch Name:'),
        'Combined Batch 1'
      )
      userEvent.click(screen.getByPlaceholderText('Select batches...'))
      const options = (await screen.findByText('Batch 3')).closest(
        '.bp3-menu'
      ) as HTMLElement
      // Select and remove a batch
      userEvent.click(within(options).getByText('Batch 3'))
      userEvent.click(screen.getByRole('button', { name: 'Remove' }))
      // Select and deselect a batch
      userEvent.click(within(options).getByText('Batch 4'))
      userEvent.click(within(options).getByText('Batch 4'))
      // Select two batches
      userEvent.click(screen.getByText('Batch 1'))
      userEvent.click(screen.getByText('Batch 2'))
      userEvent.click(
        screen.getByRole('button', { name: /Create Combined Batch/ })
      )

      const table = (await screen.findByText('Combined Batch 1')).closest(
        'table'
      )!
      expect(
        within(table)
          .getAllByRole('cell')
          .map(cell => cell.textContent)
      ).toEqual(['Combined Batch 1', 'Batch 1, Batch 2', 'deleteDelete'])

      userEvent.click(screen.getByRole('button', { name: /Delete/ }))
      await waitFor(() =>
        expect(screen.queryByText('Combined Batch 1')).not.toBeInTheDocument()
      )
    })
  })
})

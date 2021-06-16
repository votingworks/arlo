import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { withMockFetch, renderWithRouter } from './testUtilities'
import App from '../App'
import {
  aaApiCalls,
  jaApiCalls,
  apiCalls,
} from './MultiJurisdictionAudit/_mocks'
import { auditSettings } from './MultiJurisdictionAudit/useSetupMenuItems/_mocks'

const setupScreenCalls = [
  aaApiCalls.getRounds([]),
  aaApiCalls.getJurisdictions,
  aaApiCalls.getContests,
  aaApiCalls.getSettings(auditSettings.blank),
]

const renderView = (route: string) => renderWithRouter(<App />, { route })

describe('Home screen', () => {
  it('shows a login screen for unauthenticated users', async () => {
    const expectedCalls = [apiCalls.unauthenticatedUser]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')
      await screen.findByRole('img', { name: 'Arlo, by VotingWorks' })
      const jaLoginButton = screen.getByRole('button', {
        name: 'Log in to your audit',
      })
      expect(jaLoginButton).toHaveAttribute(
        'href',
        '/auth/jurisdictionadmin/start'
      )
      const aaLoginButton = screen.getByRole('link', {
        name: 'Log in as an admin',
      })
      expect(aaLoginButton).toHaveAttribute('href', '/auth/auditadmin/start')
    })
  })

  it('shows a message when an auth error occurs', async () => {
    const expectedCalls = [apiCalls.unauthenticatedUser]
    await withMockFetch(expectedCalls, async () => {
      renderView(
        '/?error=unauthorized&message=You+have+been+logged+out+due+to+inactivity.'
      )
      await screen.findByText('You have been logged out due to inactivity.')
    })
  })

  it('shows a list of audits and create audit form for audit admins', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getUser, // Extra call to load the list of audits
      aaApiCalls.postNewAudit({
        organizationId: 'org-id',
        auditName: 'November Presidential Election 2020',
        auditType: 'BATCH_COMPARISON',
        auditMathType: 'MACRO',
      }),
      ...setupScreenCalls,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds([]),
      ...setupScreenCalls,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getUserWithAudit,
      ...setupScreenCalls,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds([]),
      ...setupScreenCalls,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })
      screen.getByText(
        "You haven't created any audits yet for State of California"
      )

      // Try to create an audit without typing in an audit name
      screen.getByRole('heading', { name: 'New Audit' })
      const createAuditButton = screen.getByRole('button', {
        name: 'Create Audit',
      })
      userEvent.click(createAuditButton)
      const auditNameInput = screen.getByRole('textbox', { name: 'Audit name' })
      await within(auditNameInput.closest('label')!).findByText('Required')

      // Create a new audit
      await userEvent.type(
        auditNameInput,
        'November Presidential Election 2020'
      )
      expect(
        screen.getByRole('radio', { name: 'Ballot Polling' })
      ).toBeChecked()
      userEvent.click(screen.getByRole('radio', { name: 'Batch Comparison' }))
      userEvent.click(createAuditButton)

      // Should be on the setup screen
      await screen.findByText('The audit has not started.')
      expect(history.location.pathname).toEqual('/election/1/setup')

      // Go back to the home screen
      userEvent.click(screen.getByRole('button', { name: /View Audits/ }))

      // Click on the audit to go the setup screen
      userEvent.click(
        await screen.findByRole('button', {
          name: 'November Presidential Election 2020',
        })
      )
      await screen.findByText('The audit has not started.')
      expect(history.location.pathname).toEqual('/election/1/setup')
      await screen.findByText('Current file:')
    })
  })

  it('shows a list of audits and create audit form for audit admins with multiple orgs', async () => {
    const expectedCalls = [
      aaApiCalls.getUserMultipleOrgs,
      aaApiCalls.getUserMultipleOrgs,
      aaApiCalls.postNewAudit({
        organizationId: 'org-id-2',
        auditName: 'Presidential Primary',
        auditType: 'BALLOT_POLLING',
        auditMathType: 'BRAVO',
      }),
      ...setupScreenCalls,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds([]),
      ...setupScreenCalls,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')

      // Two orgs and their audits get displayed
      const californiaHeading = await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })
      within(californiaHeading.closest('div')!).getByRole('button', {
        name: 'November Presidential Election 2020',
      })
      const georgiaHeading = screen.getByRole('heading', {
        name: 'Audits - State of Georgia',
      })
      within(georgiaHeading.closest('div')!).getByText(
        "You haven't created any audits yet for State of Georgia"
      )

      // Select an organization
      const orgSelect = screen.getByRole('combobox', { name: /Organization/ })
      expect(
        screen.getByRole('option', {
          name: 'State of California',
        })
      ).toHaveProperty('selected', true)
      userEvent.selectOptions(orgSelect, [
        screen.getByRole('option', {
          name: 'State of Georgia',
        }),
      ])

      // Create a new audit
      await userEvent.type(
        screen.getByRole('textbox', { name: 'Audit name' }),
        'Presidential Primary'
      )
      userEvent.click(
        screen.getByRole('button', {
          name: 'Create Audit',
        })
      )

      // Should be on the setup screen
      await screen.findByText('The audit has not started.')
      await screen.findByText('Current file:')
    })
  })

  it('deletes an audit', async () => {
    const expectedCalls = [
      aaApiCalls.getUserWithAudit,
      aaApiCalls.getUserWithAudit, // Extra call to load the list of audits
      aaApiCalls.deleteAudit,
      aaApiCalls.getUser,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })
      userEvent.click(screen.getByRole('button', { name: 'Delete Audit' }))

      const dialog = (await screen.findByRole('heading', {
        name: /Confirm/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to delete November Presidential Election 2020?'
      )
      within(dialog).getByText('Warning: this action cannot be undone.')
      userEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))

      await waitFor(() =>
        expect(
          screen.queryByRole('button', {
            name: 'November Presidential Election 2020',
          })
        ).not.toBeInTheDocument()
      )
    })
  })

  it('should not delete audit when cancelled', async () => {
    const expectedCalls = [
      aaApiCalls.getUserWithAudit,
      aaApiCalls.getUserWithAudit, // Extra call to load the list of audits
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })
      userEvent.click(screen.getByRole('button', { name: 'Delete Audit' }))

      const dialog = (await screen.findByRole('heading', {
        name: /Confirm/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText(
        'Are you sure you want to delete November Presidential Election 2020?'
      )
      within(dialog).getByText('Warning: this action cannot be undone.')
      userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))

      await waitFor(() =>
        expect(
          screen.queryByRole('button', {
            name: 'November Presidential Election 2020',
          })
        )
      )
    })
  })

  it('creates batch comparison audits', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getUser, // Extra call to load the list of audits
      aaApiCalls.postNewAudit({
        organizationId: 'org-id',
        auditName: 'November Presidential Election 2020',
        auditType: 'BATCH_COMPARISON',
        auditMathType: 'MACRO',
      }),
      ...setupScreenCalls,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds([]),
      ...setupScreenCalls,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })

      const createAuditButton = screen.getByRole('button', {
        name: 'Create Audit',
      })

      // Create a new audit
      await userEvent.type(
        screen.getByRole('textbox', { name: 'Audit name' }),
        'November Presidential Election 2020'
      )
      userEvent.click(screen.getByRole('radio', { name: 'Batch Comparison' }))
      userEvent.click(createAuditButton)
      await screen.findByText('The audit has not started.')
    })
  })

  it('creates ballot comparison audits', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getUser, // Extra call to load the list of audits
      aaApiCalls.postNewAudit({
        organizationId: 'org-id',
        auditName: 'November Presidential Election 2020',
        auditType: 'BALLOT_COMPARISON',
        auditMathType: 'SUPERSIMPLE',
      }),
      ...setupScreenCalls,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds([]),
      ...setupScreenCalls,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })

      const createAuditButton = screen.getByRole('button', {
        name: 'Create Audit',
      })

      // Create a new audit
      await userEvent.type(
        screen.getByRole('textbox', { name: 'Audit name' }),
        'November Presidential Election 2020'
      )
      userEvent.click(screen.getByRole('radio', { name: 'Ballot Comparison' }))
      userEvent.click(createAuditButton)
      await screen.findByText('The audit has not started.')
    })
  })

  it('creates hybrid audits', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getUser, // Extra call to load the list of audits
      aaApiCalls.postNewAudit({
        organizationId: 'org-id',
        auditName: 'November Presidential Election 2020',
        auditType: 'HYBRID',
        auditMathType: 'SUITE',
      }),
      ...setupScreenCalls,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds([]),
      ...setupScreenCalls,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })

      const createAuditButton = screen.getByRole('button', {
        name: 'Create Audit',
      })

      // Create a new audit
      await userEvent.type(
        screen.getByRole('textbox', { name: 'Audit name' }),
        'November Presidential Election 2020'
      )
      userEvent.click(
        screen.getByRole('radio', {
          name: 'Hybrid (SUITE - Ballot Comparison & Ballot Polling)',
        })
      )
      userEvent.click(createAuditButton)
      await screen.findByText('The audit has not started.')
    })
  })

  it('shows a list of audits for jurisdiction admins', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.blank),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile({ file: null, processing: null }),
      jaApiCalls.getBatchTalliesFile({ file: null, processing: null }),
      jaApiCalls.getCVRSfile({ file: null, processing: null }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')

      // Two audits and their jurisdictions get displayed
      const auditOneHeading = await screen.findByRole('heading', {
        name: 'Jurisdictions - audit one',
      })
      const j1Button = within(auditOneHeading.closest('div')!).getByRole(
        'button',
        {
          name: 'Jurisdiction One',
        }
      )
      within(auditOneHeading.closest('div')!).getByRole('button', {
        name: 'Jurisdiction Three',
      })
      const auditTwoHeading = await screen.findByRole('heading', {
        name: 'Jurisdictions - audit two',
      })
      within(auditTwoHeading.closest('div')!).getByRole('button', {
        name: 'Jurisdiction Two',
      })

      // Click on a jurisdiction to go to the audit
      userEvent.click(j1Button)
      await screen.findByText('The audit has not started.')
    })
  })

  it('should not show delete button for ja users', async () => {
    const expectedCalls = [jaApiCalls.getUser]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')

      const auditOneHeading = await screen.findByRole('heading', {
        name: 'Jurisdictions - audit one',
      })

      within(auditOneHeading.closest('div')!).getByRole('button', {
        name: 'Jurisdiction One',
      })

      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: 'Delete Audit' })
        ).not.toBeInTheDocument()
      )
    })
  })

  it('show note if no audits for ja user', async () => {
    const expectedCalls = [jaApiCalls.getUserWithoutElections]
    await withMockFetch(expectedCalls, async () => {
      renderView('/')

      await screen.findByText(
        "You don't have any available audits at the moment"
      )
    })
  })

  it('redirects to audit screen if only one election exists for JA', async () => {
    const expectedCalls = [
      jaApiCalls.getUserWithOneElection,
      jaApiCalls.getSettings(auditSettings.blank),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile({ file: null, processing: null }),
      jaApiCalls.getBatchTalliesFile({ file: null, processing: null }),
      jaApiCalls.getCVRSfile({ file: null, processing: null }),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView('/')
      await screen.findByText('Audit Source Data')
      expect(container).toMatchSnapshot()
    })
  })
})

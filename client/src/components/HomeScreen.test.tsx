import React from 'react'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { withMockFetch, renderWithRouter } from './testUtilities'
import App from '../App'
import { aaApiCalls } from './MultiJurisdictionAudit/_mocks'

const apiCalls = {
  unauthenticatedUser: {
    url: '/api/me',
    response: {},
    error: {
      status: 401,
      statusText: 'UNAUTHORIZED',
    },
  },
  postNewAudit: {
    url: '/api/election/new',
    options: {
      method: 'POST',
      body: JSON.stringify({
        organizationId: 'org-id',
        auditName: 'November Presidential Election 2020',
        auditType: 'BATCH_COMPARISON',
        isMultiJurisdiction: true,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { electionId: '1' },
  },
  getUserWithAudit: {
    ...aaApiCalls.getUser,
    response: {
      ...aaApiCalls.getUser.response,
      organizations: [
        {
          id: 'org-id',
          name: 'State of California',
          elections: [
            {
              id: '1',
              auditName: 'November Presidential Election 2020',
              electionName: '',
              state: 'CA',
              isMultiJurisdiction: true,
            },
          ],
        },
      ],
    },
  },
}

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

  it('shows a list of audits and create audit form for audit admins', async () => {
    const setupScreenCalls = [
      aaApiCalls.getRounds,
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getRounds,
      aaApiCalls.getRounds,
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings,
      aaApiCalls.getSettings,
      aaApiCalls.getJurisdictionFile,
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getUser, // Extra call to load the list of audits
      apiCalls.postNewAudit,
      ...setupScreenCalls,
      apiCalls.getUserWithAudit,
      ...setupScreenCalls,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = renderView('/')
      await screen.findByRole('heading', {
        name: 'Audits - State of California',
      })
      screen.getByText(
        "You haven't created any audits yet for State of California"
      )

      // Create a new audit
      await screen.findByRole('heading', { name: 'New Audit' })
      await userEvent.type(
        screen.getByRole('textbox', { name: 'Audit name' }),
        'November Presidential Election 2020'
      )
      expect(
        screen.getByRole('radio', { name: 'Ballot Polling' })
      ).toBeChecked()
      userEvent.click(screen.getByRole('radio', { name: 'Batch Comparison' }))
      userEvent.click(screen.getByRole('button', { name: 'Create Audit' }))

      // Should be on the setup screen
      await screen.findByText('The audit has not started.')
      expect(history.location.pathname).toEqual('/election/1/setup')

      // Go back to the home screen
      userEvent.click(screen.getByRole('link', { name: 'View Audits' }))

      // Click on the audit to go the setup screen
      userEvent.click(
        await screen.findByRole('button', {
          name: 'November Presidential Election 2020',
        })
      )
      await screen.findByText('The audit has not started.')
      expect(history.location.pathname).toEqual('/election/1/setup')
    })
  })

  // TODO
  // - test form validation
  // - test AA in multiple orgs
  // - test JA screen
})

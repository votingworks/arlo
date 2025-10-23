import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { screen } from '@testing-library/react'
import App from './App'
import { withMockFetch, renderWithRouter } from './components/testUtilities'
import { dummyBoards } from './components/AuditBoard/_mocks'
import {
  jaApiCalls,
  aaApiCalls,
  mockOrganizations,
  tallyEntryApiCalls,
  tallyEntryUser,
  auditSettingsMocks,
  manifestMocks,
  talliesMocks,
} from './components/_mocks'

vi.unmock('react-toastify')

const apiMocks = {
  failedAuth: {
    url: '/api/me',
    response: { user: null, supportUser: null },
  },
  abAuth: {
    url: '/api/me',
    response: {
      user: { ...dummyBoards()[1] },
      supportUser: null,
    },
  },
}

const renderView = (route: string) => renderWithRouter(<App />, { route })

describe('App', () => {
  describe('/', () => {
    it('renders login screen when unauthenticated', async () => {
      const expectedCalls = [apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        renderView('/')
        await screen.findByRole('button', { name: 'Log in to your audit' })
        screen.getByRole('link', { name: 'Log in as an admin' })
      })
    })

    it('renders jurisdiction list when logged in as JA', async () => {
      const expectedCalls = [jaApiCalls.getUser]
      await withMockFetch(expectedCalls, async () => {
        renderView('/')
        await screen.findByRole('heading', { name: 'Active Audits' })
      })
    })

    it('renders audit list when logged in as AA', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderView('/')
        await screen.findByRole('heading', {
          name: 'Active Audits — State of California',
        })
      })
    })

    it('redirects to data entry flow when logged in as an audit board', async () => {
      const expectedCalls = [apiMocks.abAuth, apiMocks.abAuth]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/')
        await screen.findByRole('heading', {
          name: 'Audit Board #1: Member Sign-in',
        })
        expect(history.location.pathname).toEqual(
          '/election/1/audit-board/audit-board-1'
        )
      })
    })

    it('redirects to tally entry flow when logged in as a tally entry user', async () => {
      const expectedCalls = [
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/')
        await screen.findByRole('heading', { name: 'Tally Entry Login' })
        expect(history.location.pathname).toEqual('/tally-entry')
      })
    })
  })

  describe('/election/:electionId/jurisdiction/:jurisdictionId', () => {
    it('redirects to login screen when unauthenticated', async () => {
      const expectedCalls = [apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView(
          '/election/1/jurisdiction/jurisdiction-id-1'
        )
        await screen.findByRole('button', { name: 'Log in to your audit' })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('renders jurisdiction screen when logged in as JA', async () => {
      const expectedCalls = [
        jaApiCalls.getUser,
        jaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
        jaApiCalls.getRounds([]),
        jaApiCalls.getBallotManifestFile(manifestMocks.empty),
        jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderView('/election/1/jurisdiction/jurisdiction-id-1')
        await screen.findByText(/Jurisdiction One/)
        screen.getByText(/audit one/)
      })
    })

    it('redirects to home when logged in as AA', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView(
          '/election/1/jurisdiction/jurisdiction-id-1'
        )
        await screen.findByRole('heading', {
          name: 'Active Audits — State of California',
        })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('redirects to data entry flow when logged in as an audit board', async () => {
      const expectedCalls = [apiMocks.abAuth, apiMocks.abAuth]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView(
          '/election/1/jurisdiction/jurisdiction-id-1'
        )
        await screen.findByRole('heading', {
          name: 'Audit Board #1: Member Sign-in',
        })
        expect(history.location.pathname).toEqual(
          '/election/1/audit-board/audit-board-1'
        )
      })
    })

    it('redirects to tally entry when logged in as tally entry user', async () => {
      const expectedCalls = [
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView(
          '/election/1/jurisdiction/jurisdiction-id-1'
        )
        await screen.findByRole('heading', { name: 'Tally Entry Login' })
        expect(history.location.pathname).toEqual('/tally-entry')
      })
    })
  })

  describe('/election/:electionId/audit-board/:auditBoardId', () => {
    it('redirects to login screen when unauthenticated', async () => {
      const expectedCalls = [apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/election/1/audit-board/audit-board-1')
        await screen.findByRole('button', { name: 'Log in to your audit' })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('redirects to home when logged in as JA', async () => {
      const expectedCalls = [jaApiCalls.getUser]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/election/1/audit-board/audit-board-1')
        await screen.findByRole('heading', { name: 'Active Audits' })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('redirects to home when logged in as AA', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/election/1/audit-board/audit-board-1')
        await screen.findByRole('heading', {
          name: 'Active Audits — State of California',
        })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('redirects to tally entry when logged in as tally entry user', async () => {
      const expectedCalls = [
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/election/1/audit-board/audit-board-1')
        await screen.findByRole('heading', { name: 'Tally Entry Login' })
        expect(history.location.pathname).toEqual('/tally-entry')
      })
    })

    it('renders data entry flow when logged in as an audit board', async () => {
      const expectedCalls = [apiMocks.abAuth, apiMocks.abAuth]
      await withMockFetch(expectedCalls, async () => {
        renderView('/election/1/audit-board/audit-board-1')
        await screen.findByRole('heading', {
          name: 'Audit Board #1: Member Sign-in',
        })
      })
    })
  })

  describe('/tally-entry', () => {
    it('renders tally entry flow when logged in as tally entry user', async () => {
      const expectedCalls = [
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
        tallyEntryApiCalls.getUser(tallyEntryUser.initial),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderView('/tally-entry')
        await screen.findByRole('heading', { name: 'Tally Entry Login' })
      })
    })

    it('shows an error message when unauthenticated', async () => {
      const expectedCalls = [apiMocks.failedAuth, apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        renderView('/tally-entry')
        await screen.findByRole('heading', { name: 'You’re logged out' })
      })
    })

    it('redirects to home when logged in as AA', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/tally-entry')
        await screen.findByRole('heading', {
          name: 'Active Audits — State of California',
        })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('redirects to home when logged in as JA', async () => {
      const expectedCalls = [jaApiCalls.getUser, jaApiCalls.getUser]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/tally-entry')
        await screen.findByRole('heading', { name: 'Active Audits' })
        expect(history.location.pathname).toEqual('/')
      })
    })

    it('redirects to audit board data entry when logged in as an audit board', async () => {
      const expectedCalls = [apiMocks.abAuth, apiMocks.abAuth, apiMocks.abAuth]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderView('/tally-entry')
        await screen.findByRole('heading', {
          name: 'Audit Board #1: Member Sign-in',
        })
        expect(history.location.pathname).toEqual(
          '/election/1/audit-board/audit-board-1'
        )
      })
    })
  })
})

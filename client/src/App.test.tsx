import React from 'react'
import { screen } from '@testing-library/react'
import App from './App'
import { withMockFetch, renderWithRouter } from './components/testUtilities'
import { dummyBoards } from './components/AuditBoard/_mocks'
import { jaApiCalls, aaApiCalls, mockOrganizations } from './components/_mocks'
import {
  auditSettings,
  manifestMocks,
  talliesMocks,
} from './components/AuditAdmin/useSetupMenuItems/_mocks'

jest.unmock('react-toastify')

const apiMocks = {
  failedAuth: {
    url: '/api/me',
    response: { user: null, supportUser: null },
  },
  abAuth: {
    url: '/api/me',
    response: {
      user: { type: 'audit_board', ...dummyBoards()[1] },
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
        await screen.findByRole('heading', {
          name: 'Jurisdictions - audit one',
        })
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
          name: 'Audits - State of California',
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
        jaApiCalls.getSettings(auditSettings.batchComparisonAll),
        jaApiCalls.getRounds([]),
        jaApiCalls.getBallotManifestFile(manifestMocks.empty),
        jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderView('/election/1/jurisdiction/jurisdiction-id-1')
        await screen.findByText('Jurisdiction: Jurisdiction One')
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
          name: 'Audits - State of California',
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
        await screen.findByRole('heading', {
          name: 'Jurisdictions - audit one',
        })
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
          name: 'Audits - State of California',
        })
        expect(history.location.pathname).toEqual('/')
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
})

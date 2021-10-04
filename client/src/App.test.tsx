import React from 'react'
import { screen, render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'
import { withMockFetch, renderWithRouter } from './components/testUtilities'
import { dummyBoards } from './components/DataEntry/_mocks'
import {
  auditSettings,
  manifestMocks,
  talliesMocks,
} from './components/MultiJurisdictionAudit/useSetupMenuItems/_mocks'
import {
  jaApiCalls,
  aaApiCalls,
  mockOrganizations,
} from './components/MultiJurisdictionAudit/_mocks'

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

    it('renders ja logged in properly', async () => {
      const expectedCalls = [jaApiCalls.getUser]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/')
        expect(
          (await screen.findAllByAltText('Arlo, by VotingWorks')).length
        ).toBe(2)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders aa logged in properly', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/')
        expect(
          (await screen.findAllByAltText('Arlo, by VotingWorks')).length
        ).toBe(2)
        expect(container).toMatchSnapshot()
      })
    })

    it('when logged in as an audit board, shows the login screen', async () => {
      const expectedCalls = [apiMocks.abAuth, apiMocks.abAuth]
      await withMockFetch(expectedCalls, async () => {
        renderView('/')
        await screen.findAllByText(/Audit Board #1/)
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

    it('renders ja logged in properly', async () => {
      const expectedCalls = [jaApiCalls.getUser]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/audit-board/audit-board-1'
        )
        expect(
          (await screen.findAllByAltText('Arlo, by VotingWorks')).length
        ).toBe(2)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders aa logged in properly', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/audit-board/audit-board-1'
        )
        expect(
          (await screen.findAllByAltText('Arlo, by VotingWorks')).length
        ).toBe(2)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ab logged in properly', async () => {
      const expectedCalls = [apiMocks.abAuth, apiMocks.abAuth]
      await withMockFetch(expectedCalls, async () => {
        const { container } = render(
          <MemoryRouter
            initialEntries={['/election/1/audit-board/audit-board-1']}
            initialIndex={0}
          >
            <App />
          </MemoryRouter>
        )
        await screen.findByText('Audit Board #1: Member Sign-in')
        expect(container).toMatchSnapshot()
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

    it('renders ja logged in properly', async () => {
      const expectedCalls = [
        jaApiCalls.getUser,
        jaApiCalls.getSettings(auditSettings.batchComparisonAll),
        jaApiCalls.getRounds([]),
        jaApiCalls.getBallotManifestFile(manifestMocks.empty),
        jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/jurisdiction/jurisdiction-id-1'
        )
        expect(
          (await screen.findAllByAltText('Arlo, by VotingWorks')).length
        ).toBe(2)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders aa logged in properly', async () => {
      const expectedCalls = [
        aaApiCalls.getUser,
        aaApiCalls.getOrganizations(mockOrganizations.oneOrgNoAudits),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/jurisdiction/jurisdiction-id-1'
        )
        await screen.findByText('New Audit')
        expect(container).toMatchSnapshot()
      })
    })
  })
})

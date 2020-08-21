import React from 'react'
import { screen, render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'
import { withMockFetch, renderWithRouter } from './components/testUtilities'
import { IUserMeta } from './types'
import { dummyBoards } from './components/DataEntry/_mocks'
import {
  // jaApiCalls,
  aaApiCalls,
} from './components/MultiJurisdictionAudit/_mocks'
// import { manifestMocks } from './components/MultiJurisdictionAudit/useSetupMenuItems/_mocks'

jest.unmock('react-toastify')

const userMocks: { [key in 'ja' | 'aa']: IUserMeta } = {
  ja: {
    name: 'Han Solo',
    email: 'falcon@gmail.com',
    type: 'jurisdiction_admin',
    organizations: [],
    jurisdictions: [],
  },
  aa: {
    name: 'Leia Organa',
    email: 'princess@rebelalliance.com',
    type: 'audit_admin',
    organizations: [],
    jurisdictions: [],
  },
}

const apiMocks = {
  failedAuth: {
    url: '/api/me',
    response: {},
    error: {
      status: 401,
      statusText: 'UNAUTHORIZED',
    },
  },
  successAuth: (response: IUserMeta) => ({
    url: '/api/me',
    response,
  }),
  abAuth: {
    url: '/api/me',
    response: { type: 'AUDIT_BOARD', ...dummyBoards()[1] },
  },
}

const renderView = (route: string) => renderWithRouter(<App />, { route })

describe('App', () => {
  describe('/', () => {
    it('renders unauthenticated properly', async () => {
      const expectedCalls = [apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/')
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ja logged in properly', async () => {
      const expectedCalls = [apiMocks.successAuth(userMocks.ja)]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/')
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders aa logged in properly', async () => {
      const expectedCalls = [apiMocks.successAuth(userMocks.aa)]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/')
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })
  })

  describe('/election/:electionId/audit-board/:auditBoardId', () => {
    it('renders unauthenticated properly', async () => {
      const expectedCalls = [apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/audit-board/audit-board-1'
        )
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ja logged in properly', async () => {
      const expectedCalls = [apiMocks.successAuth(userMocks.ja)]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/audit-board/audit-board-1'
        )
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders aa logged in properly', async () => {
      const expectedCalls = [apiMocks.successAuth(userMocks.aa)]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView(
          '/election/1/audit-board/audit-board-1'
        )
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it.skip('renders ab logged in properly', async () => {
      const expectedCalls = [apiMocks.abAuth]
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
    it('renders unauthenticated properly', async () => {
      const expectedCalls = [apiMocks.failedAuth]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/election/1/jurisdiction-id-1/1')
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ja logged in properly', async () => {
      const expectedCalls = [apiMocks.successAuth(userMocks.ja)]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/election/1/jurisdiction-id-1/1')
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders aa logged in properly', async () => {
      const expectedCalls = [
        apiMocks.successAuth(userMocks.aa),
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
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderView('/election/1/jurisdiction-id-1/1')
        await screen.findByAltText('Arlo, by VotingWorks')
        expect(container).toMatchSnapshot()
      })
    })
  })
})

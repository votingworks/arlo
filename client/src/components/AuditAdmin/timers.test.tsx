/**
 * These tests are segregated because they were creating unreliable interference
 */

import React, { ReactElement } from 'react'
import { screen, act } from '@testing-library/react'
import { Route } from 'react-router-dom'
import FakeTimers from '@sinonjs/fake-timers'
import { QueryClientProvider } from 'react-query'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import AuditAdminView from './AuditAdminView'
import {
  renderWithRouter,
  withMockFetch,
  createQueryClient,
} from '../testUtilities'
import { aaApiCalls, auditSettingsMocks, contestMocks } from '../_mocks'

// AuditAdminView will only be rendered once the user is logged in, so
// we simulate that.
const AuditAdminViewWithAuth: React.FC = () => {
  const auth = useAuthDataContext()
  return auth ? <AuditAdminView /> : null
}

const renderWithRoute = (route: string, component: ReactElement) =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <Route path="/election/:electionId/:view">
        <AuthDataProvider>{component}</AuthDataProvider>
      </Route>
    </QueryClientProvider>,
    {
      route,
    }
  )

describe('timers', () => {
  let clock = FakeTimers.install()
  beforeEach(() => {
    clock = FakeTimers.install()
  })
  afterEach(() => {
    clock.uninstall()
  })
  it('refreshes every five minutes on progress', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
      aaApiCalls.getLastLoginByJurisdiction(),
      aaApiCalls.getMapData,
      aaApiCalls.getRounds([]),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getLastLoginByJurisdiction(),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderWithRoute('/election/1/progress', <AuditAdminViewWithAuth />)
      await act(async () => {
        await clock.nextAsync()
      })
      await screen.findByText('Will refresh in 5 minutes')
      await act(async () => {
        await clock.tickAsync(1000 * 60)
      })
      await screen.findByText('Will refresh in 4 minutes')
      await act(async () => {
        await clock.tickAsync(1000 * 60 * 4)
      })
      await screen.findByText('Will refresh in 5 minutes')
    })
  })
})

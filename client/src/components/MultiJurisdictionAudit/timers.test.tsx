/**
 * These tests are segregated from index.test.tsx because they were creating unreliable interference
 */

import React, { useContext } from 'react'
import { screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import { AuditAdminView } from './index'
import { renderWithRouter, withMockFetch } from '../testUtilities'
import AuthDataProvider, { AuthDataContext } from '../UserContext'
import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { aaApiCalls } from './_mocks'

const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
const getRoundStatusMock = getRoundStatus as jest.Mock

jest.mock('./useSetupMenuItems/getJurisdictionFileStatus')
jest.mock('./useSetupMenuItems/getRoundStatus')
getJurisdictionFileStatusMock.mockReturnValue('PROCESSED')
getRoundStatusMock.mockReturnValue(false)

// AuditAdminView will only be rendered once the user is logged in, so
// we simulate that.
const AuditAdminViewWithAuth: React.FC = () => {
  const { isAuthenticated } = useContext(AuthDataContext)
  return isAuthenticated ? <AuditAdminView /> : null
}

const renderWithRoute = () =>
  renderWithRouter(
    <Route path="/election/:electionId/:view">
      <AuthDataProvider>
        <AuditAdminViewWithAuth />
      </AuthDataProvider>
    </Route>,
    {
      route: '/election/1/progress',
    }
  )

const loadEach = [
  aaApiCalls.getRounds,
  aaApiCalls.getJurisdictions,
  aaApiCalls.getContests,
  aaApiCalls.getSettings,
]

describe('timers', () => {
  const j = (function* idMaker() {
    let index = 0
    while (true) yield (index += 30000) // forces it to jump past the check in the first tick
  })()
  const dateSpy = jest
    .spyOn(Date, 'now')
    .mockImplementation(() => j.next().value)

  afterAll(() => {
    dateSpy.mockRestore()
  })

  it('refreshes every five minutes on progress', async () => {
    const expectedCalls = [aaApiCalls.getUser, ...loadEach, ...loadEach]
    await withMockFetch(expectedCalls, async () => {
      renderWithRoute()
      await screen.findByText('Refreshed 59 minutes ago') // the resulting value after the refresh is odd in the test environment
    })
  })
})

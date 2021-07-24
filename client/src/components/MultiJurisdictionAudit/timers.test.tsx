/**
 * These tests are segregated from index.test.tsx because they were creating unreliable interference
 */

import React, { ReactElement } from 'react'
import { screen, act } from '@testing-library/react'
import { Route } from 'react-router-dom'
import FakeTimers from '@sinonjs/fake-timers'
import userEvent from '@testing-library/user-event'
import { AuditAdminView } from './index'
import { renderWithRouter, withMockFetch } from '../testUtilities'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { aaApiCalls } from './_mocks'
import { auditSettings, roundMocks } from './useSetupMenuItems/_mocks'
import { sampleSizeMock } from './AASetup/Review/_mocks'

const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
const getRoundStatusMock = getRoundStatus as jest.Mock

jest.mock('./useSetupMenuItems/getJurisdictionFileStatus')
jest.mock('./useSetupMenuItems/getRoundStatus')
getJurisdictionFileStatusMock.mockReturnValue('PROCESSED')
getRoundStatusMock.mockReturnValue(false)

// AuditAdminView will only be rendered once the user is logged in, so
// we simulate that.
const AuditAdminViewWithAuth: React.FC = () => {
  const auth = useAuthDataContext()
  return auth ? <AuditAdminView /> : null
}

const renderWithRoute = (route: string, component: ReactElement) =>
  renderWithRouter(
    <Route path="/election/:electionId/:view">
      <AuthDataProvider>{component}</AuthDataProvider>
    </Route>,
    {
      route,
    }
  )

const loadEach = [
  aaApiCalls.getRounds([]),
  aaApiCalls.getJurisdictions,
  aaApiCalls.getContests,
  aaApiCalls.getSettings(auditSettings.all),
]

describe('timers', () => {
  let clock = FakeTimers.install()
  beforeEach(() => {
    clock = FakeTimers.install()
  })
  afterEach(() => clock.uninstall())
  it('refreshes every five minutes on progress', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getMapData,
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderWithRoute('/election/1/progress', <AuditAdminViewWithAuth />)
      await act(async () => {
        await clock.nextAsync()
      })
      screen.getByText('Will refresh in 5 minutes')
      await act(async () => {
        await clock.tickAsync(1000 * 60)
      })
      screen.getByText('Will refresh in 4 minutes')
      await act(async () => {
        // Five minutes minus the ten seconds we already ticked
        await clock.tickAsync(1000 * (60 * 5 - 10))
      })
      screen.getByText('Will refresh in 5 minutes')
    })
  })

  it('shows a spinner while sample is being drawn', async () => {
    const loadAfterLaunch = [
      aaApiCalls.getRounds(roundMocks.drawSampleInProgress),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings(auditSettings.all),
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadAfterLaunch,
      ...loadAfterLaunch,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderWithRoute('/election/1/progress', <AuditAdminViewWithAuth />)
      await act(async () => {
        await clock.nextAsync()
      })
      await screen.findByRole('heading', {
        name: 'Drawing a random sample of ballots...',
      })
      screen.getByText(
        'For large elections, this can take a couple of minutes.'
      )
    })
  })

  it('shows a spinner while sample sizes are computed', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getContests,
      ...loadEach,
      aaApiCalls.getSampleSizes,
      { ...aaApiCalls.getSampleSizes, response: sampleSizeMock },
    ]
    await withMockFetch(expectedCalls, async () => {
      renderWithRoute('/election/1/setup', <AuditAdminViewWithAuth />)
      await act(async () => {
        await clock.nextAsync()
      })
      await screen.findByRole('heading', { name: 'Audit Setup' })
      userEvent.click(screen.getByText('Review & Launch'))
      await screen.findByRole('heading', { name: 'Sample Size' })
      screen.getByText('Loading sample size options...')

      await act(async () => {
        await clock.tickAsync(1000 * 60)
      })
      screen.getByText(
        'Choose the initial sample size for each contest you would like to use for Round 1 of the audit from the options below.'
      )
    })
  })
})

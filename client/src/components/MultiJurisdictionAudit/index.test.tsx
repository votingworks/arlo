import React, { useContext } from 'react'
import { waitFor, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  BrowserRouter as Router,
  Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import {
  AuditAdminView,
  JurisdictionAdminView,
  prettifyRefreshStatus,
} from './index'
import {
  manifestMocks,
  talliesMocks,
  cvrsMocks,
  manifestFile,
  talliesFile,
  auditSettings,
  roundMocks,
} from './useSetupMenuItems/_mocks'
import {
  routerTestProps,
  withMockFetch,
  renderWithRouter,
} from '../testUtilities'
import AuthDataProvider, { AuthDataContext } from '../UserContext'
import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { jaApiCalls, aaApiCalls } from './_mocks'

const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
const getRoundStatusMock = getRoundStatus as jest.Mock

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

jest.mock('./useSetupMenuItems/getJurisdictionFileStatus')
jest.mock('./useSetupMenuItems/getRoundStatus')
getJurisdictionFileStatusMock.mockReturnValue('PROCESSED')
getRoundStatusMock.mockReturnValue(false)

afterEach(() => {
  paramsMock.mockReturnValue({
    electionId: '1',
    view: 'setup',
  })
})

describe('AA setup flow', () => {
  // AuditAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const AuditAdminViewWithAuth: React.FC = () => {
    const { isAuthenticated } = useContext(AuthDataContext)
    return isAuthenticated ? <AuditAdminView /> : null
  }

  const loadEach = [
    aaApiCalls.getRounds([]),
    aaApiCalls.getJurisdictions,
    aaApiCalls.getContests,
    aaApiCalls.getSettings(auditSettings.all),
  ]

  it('sidebar changes stages', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText, getByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })

      fireEvent.click(getByText('Audit Settings'), { bubbles: true })

      await waitFor(() => {
        expect(queryAllByText('Audit Settings').length).toBe(2)
      })
    })
  })

  it.skip('next and back buttons change stages', async () => {
    // TEST TODO
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getSettings(auditSettings.all),
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.putSettings(auditSettings.all),
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getContests,
      aaApiCalls.getSampleSizes,
      aaApiCalls.getSettings(auditSettings.all),
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText, getByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })

      fireEvent.click(getByText('Audit Settings'), { bubbles: true })

      await waitFor(() => {
        expect(queryAllByText('Audit Settings').length).toBe(2)
      })

      fireEvent.click(getByText('Save & Next'))
      await waitFor(() => {
        expect(queryAllByText('Review & Launch').length).toBe(2)
      })
      fireEvent.click(getByText('Back'))
      await waitFor(() => {
        expect(queryAllByText('Audit Settings').length).toBe(2)
      })
    })
  })

  it('renders sidebar when authenticated on /setup', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container, queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })
      expect(container).toMatchSnapshot()
    })
  })

  it('renders sidebar when authenticated on /progress', async () => {
    paramsMock.mockReturnValue({
      electionId: '1',
      view: 'progress',
    })
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container, queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Jurisdictions').length).toBe(1)
        expect(container).toMatchSnapshot()
      })
    })
  })

  it('redirects to /progress after audit is launched', async () => {
    const loadAfterLaunch = [
      aaApiCalls.getRounds(roundMocks.singleIncomplete),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings(auditSettings.all),
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadAfterLaunch,
      ...loadAfterLaunch,
      ...loadAfterLaunch,
    ]
    const routeProps = routerTestProps('/election/1', { electionId: '1' })
    await withMockFetch(expectedCalls, async () => {
      paramsMock.mockReturnValue({
        electionId: '1',
        view: '',
      })
      render(
        <AuthDataProvider>
          <RegularRouter {...routeProps}>
            <AuditAdminViewWithAuth />
          </RegularRouter>
        </AuthDataProvider>
      )
      await waitFor(() => {
        expect(routeProps.history.location.pathname).toEqual(
          '/election/1/progress'
        )
      })
    })
  })
})

describe('JA setup', () => {
  // JurisdictionAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const JurisdictionAdminViewWithAuth: React.FC = () => {
    const { isAuthenticated } = useContext(AuthDataContext)
    return isAuthenticated ? <JurisdictionAdminView /> : null
  }

  const renderView = () =>
    renderWithRouter(
      <AuthDataProvider>
        <JurisdictionAdminViewWithAuth />
      </AuthDataProvider>,
      {
        route: '/election/1/jurisdiction/jurisdiction-id-1/setup',
      }
    )

  beforeEach(() => {
    paramsMock.mockReturnValue({
      electionId: '1',
      jurisdictionId: 'jurisdiction-id-1',
      view: 'setup',
    })
  })

  it('renders initial state', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Audit Source Data')
      expect(container).toMatchSnapshot()
    })
  })

  it('submits ballot manifest', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Audit Source Data')
      const csvInput = screen.getAllByLabelText('Select a CSV...')[0]
      fireEvent.change(csvInput, { target: { files: [] } })
      fireEvent.blur(csvInput)
      await waitFor(() =>
        expect(screen.queryByText('You must upload a file')).toBeTruthy()
      )
      fireEvent.change(csvInput, { target: { files: [manifestFile] } })
      await waitFor(() =>
        expect(screen.queryByText('You must upload a file')).toBeFalsy()
      )
      await waitFor(() =>
        expect(screen.queryAllByLabelText('Select a CSV...').length).toBe(1)
      )
      await waitFor(() =>
        expect(screen.queryByLabelText('manifest.csv')).toBeTruthy()
      )
      userEvent.click(screen.getAllByText('Upload File')[0])
      await screen.findByText('Current file:')
      expect(container).toMatchSnapshot()
    })
  })

  it('submits batch tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      jaApiCalls.putTallies,
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Audit Source Data')
      const csvInput = screen.getByLabelText('Select a CSV...')
      fireEvent.change(csvInput, { target: { files: [] } })
      fireEvent.blur(csvInput)
      await waitFor(() =>
        expect(screen.queryByText('You must upload a file')).toBeTruthy()
      )
      fireEvent.change(csvInput, { target: { files: [talliesFile] } })
      await waitFor(() =>
        expect(screen.queryByText('You must upload a file')).toBeFalsy()
      )
      await waitFor(() =>
        expect(screen.queryByLabelText('Select a CSV...')).toBeFalsy()
      )
      await waitFor(() =>
        expect(screen.queryByLabelText('tallies.csv')).toBeTruthy()
      )
      userEvent.click(screen.getByText('Upload File'))
      await waitFor(() =>
        expect(screen.getAllByText('Replace File').length).toBe(2)
      )
      expect(container).toMatchSnapshot()
    })
  })
})

describe('prettifyRefreshStatus', () => {
  it('handles recent values', () => {
    expect(prettifyRefreshStatus(0)).toBe('Will refresh in 5 minutes')
    expect(prettifyRefreshStatus(9000)).toBe('Will refresh in 5 minutes')
  })

  it('handles minute increments', () => {
    expect(prettifyRefreshStatus(60000)).toBe('Will refresh in 4 minutes')
    expect(prettifyRefreshStatus(120000)).toBe('Will refresh in 3 minutes')
    expect(prettifyRefreshStatus(180000)).toBe('Will refresh in 2 minutes')
    expect(prettifyRefreshStatus(240000)).toBe('Will refresh in 1 minute')
  })

  it('handles ten second increments', () => {
    expect(prettifyRefreshStatus(250000)).toBe('Will refresh in 50 seconds')
    expect(prettifyRefreshStatus(260001)).toBe('Will refresh in 40 seconds')
    expect(prettifyRefreshStatus(270001)).toBe('Will refresh in 30 seconds')
    expect(prettifyRefreshStatus(280001)).toBe('Will refresh in 20 seconds')
    expect(prettifyRefreshStatus(290001)).toBe('Will refresh in 10 seconds')
  })
})

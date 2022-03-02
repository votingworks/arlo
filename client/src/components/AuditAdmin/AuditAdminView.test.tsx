import React from 'react'
import { waitFor, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  BrowserRouter as Router,
  Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import AuditAdminView from './AuditAdminView'
import {
  jurisdictionFileMocks,
  standardizedContestsFileMocks,
  auditSettings,
  roundMocks,
} from './useSetupMenuItems/_mocks'
import { routerTestProps, withMockFetch } from '../testUtilities'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { aaApiCalls } from '../_mocks'
import {
  jurisdictionFile,
  jurisdictionErrorFile,
  standardizedContestsFile,
} from './Setup/Participants/_mocks'

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

jest.mock('axios')

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
    const auth = useAuthDataContext()
    return auth ? <AuditAdminView /> : null
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

  it('renders sidebar when authenticated on /setup', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
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

  it('get empty jurisdiction file intiially', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
        screen.getByLabelText('Select a CSV...')
      })
    })
  })

  it('get jurisdisction file get if exists', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryByText, queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
        expect(queryByText(/Current file/))
      })
    })
  })

  it('jurisdisction file upload success', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
      aaApiCalls.putJurisdictionFile,
      aaApiCalls.getJurisdictionFileWithResponse(
        jurisdictionFileMocks.processed
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })
      const jurisdisctionInput = screen.getByLabelText('Select a CSV...')
      const jurisdictionButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      userEvent.click(jurisdictionButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(jurisdisctionInput, jurisdictionFile)
      userEvent.click(jurisdictionButton)
      await screen.findByText(/Uploaded/)
    })
  })

  it('jurisdisction file upload with error', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
      aaApiCalls.putJurisdictionErrorFile,
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })
      const jurisdisctionInput = screen.getByLabelText('Select a CSV...')
      const jurisdictionButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      userEvent.click(jurisdictionButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(jurisdisctionInput, jurisdictionErrorFile)
      userEvent.click(jurisdictionButton)
      await screen.findByText('Invalid CSV')
    })
  })

  it('standardized contests file upload success', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadEach,
      ...loadEach,
      aaApiCalls.getSettings(auditSettings.blankBallotComparison),
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.empty
      ),
      aaApiCalls.putStandardizedContestsFile,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.processed
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      // check file upload of jurisdiction
      await screen.findByText(/Uploaded/)
      const standardizedContestInput = screen.getByLabelText('Select a CSV...')
      const standardizedContestButton = screen.getByRole('button', {
        name: 'Upload File',
      })
      userEvent.click(standardizedContestButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(standardizedContestInput, standardizedContestsFile)
      userEvent.click(standardizedContestButton)
      await screen.findByText(/Uploaded/)
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

  it('shows an error and undo button if drawing the sample fails', async () => {
    const loadAfterLaunch = [
      aaApiCalls.getRounds(roundMocks.drawSampleErrored),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings(auditSettings.all),
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      ...loadAfterLaunch,
      ...loadAfterLaunch,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      {
        url: '/api/election/1/round/round-1',
        options: { method: 'DELETE' },
        response: { status: 'ok' },
      },
      aaApiCalls.getRounds(roundMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )
      await screen.findByRole('heading', {
        name: 'Arlo could not draw the sample',
      })
      screen.getByText(
        'Please contact our support team for help resolving this issue.'
      )
      screen.getByText('Error: something went wrong')

      userEvent.click(screen.getByRole('button', { name: 'Undo Audit Launch' }))
      await screen.findByText('The audit has not started.')
    })
  })
})

import React from 'react'
import {
  waitFor,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  BrowserRouter as Router,
  Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import {
  AuditAdminView,
  JurisdictionAdminView,
  prettifyRefreshStatus,
} from './index'
import {
  jurisdictionFileMocks,
  standardizedContestsFileMocks,
  manifestMocks,
  talliesMocks,
  cvrsMocks,
  manifestFile,
  talliesFile,
  auditSettings,
  roundMocks,
  cvrsFile,
} from './useSetupMenuItems/_mocks'
import {
  routerTestProps,
  withMockFetch,
  renderWithRouter,
  serverError,
} from '../testUtilities'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { jaApiCalls, aaApiCalls } from './_mocks'
import {
  jurisdictionFile,
  jurisdictionErrorFile,
  standardizedContestsFile,
} from './AASetup/Participants/_mocks'

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

describe('JA setup', () => {
  // JurisdictionAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const JurisdictionAdminViewWithAuth: React.FC = () => {
    const auth = useAuthDataContext()
    return auth ? <JurisdictionAdminView /> : null
  }

  const renderView = () =>
    renderWithRouter(
      <AuthDataProvider>
        <JurisdictionAdminViewWithAuth />
        <ToastContainer />
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
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Audit Source Data')
      expect(container).toMatchSnapshot()
    })
  })

  it('submits ballot manifest and deletes it', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.all),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.deleteManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')

      const uploadButton = screen.getByRole('button', { name: 'Upload File' })
      userEvent.click(uploadButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(screen.getByLabelText('Select a CSV...'), manifestFile)
      userEvent.click(uploadButton)
      await screen.findByText('Uploaded at 6/8/2020, 9:39:14 PM.')

      // We test delete after submit so that we can check that the input is
      // cleared of the originally submitted file
      const deleteButton = await screen.findByRole('button', {
        name: 'Delete File',
      })
      userEvent.click(deleteButton)
      await screen.findByRole('button', { name: 'Upload File' })
      screen.getByLabelText('Select a CSV...')
    })
  })

  it('submits batch tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.putTallies,
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      const talliesInput = screen.getByLabelText('Select a CSV...')
      const talliesButton = screen.getByRole('button', { name: 'Upload File' })

      userEvent.click(talliesButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(talliesInput, talliesFile)
      userEvent.click(talliesButton)
      await screen.findByText('Uploaded at 7/8/2020, 9:39:14 PM.')
    })
  })

  it('toasts error when uploading batch tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      serverError('putTallies', jaApiCalls.putTallies),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      userEvent.upload(screen.getByLabelText('Select a CSV...'), talliesFile)
      userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      const toast = await screen.findByRole('alert')
      expect(toast).toHaveTextContent('something went wrong: putTallies')
    })
  })

  it('displays errors on invalid batch tallies upload', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      jaApiCalls.putTallies,
      jaApiCalls.getBatchTalliesFile(talliesMocks.processing),
      jaApiCalls.getBatchTalliesFile(talliesMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      expect(screen.getAllByText(/Uploaded/)).toHaveLength(2)

      // Replace & upload errored batch tallies
      userEvent.click(
        screen.getAllByRole('button', {
          name: 'Replace File',
        })[1]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a CSV...'),
        talliesFile
      )
      await waitFor(() => {
        userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      })
      await screen.findByText(/Uploaded/)
      await screen.findByText('Invalid CSV')
    })
  })

  it('displays errors after reprocessing batch tallies on replacing Manifest', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.processed),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.processing),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      expect(screen.getAllByText(/Uploaded/)).toHaveLength(2)

      // Upload a new manifest
      userEvent.click(
        screen.getAllByRole('button', { name: 'Replace File' })[0]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a CSV...'),
        manifestFile
      )
      await waitFor(() => {
        userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      })
      await screen.findByText(/Uploaded/)
      await screen.findByText('Invalid CSV')
    })
  })

  it('submits CVRs', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
      jaApiCalls.putCVRs,
      jaApiCalls.getCVRSfile(cvrsMocks.processing),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      const fileTypeSelect = screen.getByLabelText(/CVR File Type:/)
      within(fileTypeSelect).getByRole('option', {
        name: 'Dominion',
        selected: true,
      })
      userEvent.selectOptions(
        fileTypeSelect,
        screen.getByRole('option', { name: 'ClearBallot' })
      )

      const cvrsInput = screen.getByLabelText('Select a CSV...')
      const cvrsButton = screen.getByRole('button', { name: 'Upload File' })

      userEvent.click(cvrsButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(cvrsInput, cvrsFile)
      userEvent.click(cvrsButton)

      await screen.findByText('Uploading...')
      expect(fileTypeSelect).toBeDisabled()

      await screen.findByText('Processing...')
      expect(fileTypeSelect).toBeDisabled()

      await screen.findByText('Uploaded at 11/18/2020, 9:39:14 PM.')
      expect(fileTypeSelect).toBeDisabled()
      within(fileTypeSelect).getByRole('option', {
        name: 'ClearBallot',
        selected: true,
      })
    })
  })

  it('after deleting CVRs, keeps last selected CVR file type ', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      jaApiCalls.deleteCVRs,
      jaApiCalls.getCVRSfile(cvrsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Uploaded at 6/8/2020, 9:39:14 PM.')
      screen.getByRole('option', { name: 'ClearBallot', selected: true })
      userEvent.click(screen.getAllByRole('button', { name: 'Delete File' })[1])
      await screen.findByText('Select a CSV...')
      screen.getByRole('option', { name: 'ClearBallot', selected: true })
    })
  })

  it('displays errors on invalid CVRs upload', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      jaApiCalls.putCVRs,
      jaApiCalls.getCVRSfile(cvrsMocks.processing),
      jaApiCalls.getCVRSfile(cvrsMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      expect(screen.getAllByText(/Uploaded/)).toHaveLength(2)

      // Replace & upload errored CVRs
      userEvent.click(
        screen.getAllByRole('button', {
          name: 'Replace File',
        })[1]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a CSV...'),
        cvrsFile
      )
      await waitFor(() => {
        userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      })
      await screen.findByText(/Uploaded/)
      await screen.findByText('Invalid CSV')
    })
  })

  it('displays errors after reprocessing CVRs on replacing Manifest', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.ballotComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.processed),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.processing),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getCVRSfile(cvrsMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      expect(screen.getAllByText(/Uploaded/)).toHaveLength(2)

      // Upload a new manifest
      userEvent.click(
        screen.getAllByRole('button', { name: 'Replace File' })[0]
      )
      userEvent.upload(
        await screen.findByLabelText('Select a CSV...'),
        manifestFile
      )
      await waitFor(() => {
        userEvent.click(screen.getByRole('button', { name: 'Upload File' }))
      })
      await screen.findByText(/Uploaded/)
      await screen.findByText('Invalid CSV')
    })
  })

  it('shows error with incorrect file', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.errored),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')
      const [manifestInput, talliesInput] = screen.getAllByLabelText(
        'Select a CSV...'
      )
      const [manifestButton, talliesButton] = screen.getAllByRole('button', {
        name: 'Upload File',
      })

      expect(talliesInput).toBeDisabled()
      expect(talliesButton).toBeDisabled()

      userEvent.click(manifestButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(manifestInput, manifestFile)
      userEvent.click(manifestButton)
      await screen.findByText('Invalid CSV')
    })
  })

  it('replaces manifest file', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getRounds([]),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getBatchTalliesFile(talliesMocks.empty),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Audit Source Data')

      const replaceButton = await screen.findByText('Replace File')
      userEvent.click(replaceButton)
      const inputFiles = await screen.findAllByText('Select a CSV...')
      expect(inputFiles).toHaveLength(2)

      const [manifestInput] = screen.getAllByLabelText('Select a CSV...')
      const [manifestButton] = screen.getAllByRole('button', {
        name: 'Upload File',
      })

      userEvent.click(manifestButton)
      await screen.findByText('You must upload a file')

      userEvent.upload(manifestInput, manifestFile)
      userEvent.click(manifestButton)
      await screen.findByText('Current file:')
    })
  })

  it('stays on the file upload screen when sample is being drawn', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.all),
      jaApiCalls.getRounds(roundMocks.drawSampleInProgress),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: 'Audit Source Data' })
      screen.getByText('The audit has not started.')
    })
  })

  it('stays on the file upload screen when drawing sample errors', async () => {
    const expectedCalls = [
      jaApiCalls.getUser,
      jaApiCalls.getSettings(auditSettings.all),
      jaApiCalls.getRounds(roundMocks.drawSampleErrored),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByRole('heading', { name: 'Audit Source Data' })
      screen.getByText('The audit has not started.')
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

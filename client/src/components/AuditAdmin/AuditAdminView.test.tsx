import React from 'react'
import { waitFor, fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, RouteProps } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import AuditAdminView from './AuditAdminView'
import {
  jurisdictionFileMocks,
  standardizedContestsFileMocks,
  auditSettings,
  roundMocks,
  manifestFile,
  manifestMocks,
  jurisdictionMocks,
} from './useSetupMenuItems/_mocks'
import {
  withMockFetch,
  renderWithRouter,
  createQueryClient,
} from '../testUtilities'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { aaApiCalls, jaApiCalls } from '../_mocks'
import {
  jurisdictionFile,
  jurisdictionErrorFile,
  standardizedContestsFile,
} from './Setup/Participants/_mocks'

const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
const getRoundStatusMock = getRoundStatus as jest.Mock

jest.mock('./useSetupMenuItems/getJurisdictionFileStatus')
jest.mock('./useSetupMenuItems/getRoundStatus')
getJurisdictionFileStatusMock.mockReturnValue('PROCESSED')
getRoundStatusMock.mockReturnValue(false)

jest.mock('axios')

// AuditAdminView will only be rendered once the user is logged in, so
// we simulate that.
const AuditAdminViewWithAuth = (props: RouteProps) => {
  const auth = useAuthDataContext()
  return auth ? <AuditAdminView {...props} /> : null
}

const render = (view = 'setup') =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <AuthDataProvider>
        <Route
          path="/election/:electionId/:view?"
          render={routeProps => <AuditAdminViewWithAuth {...routeProps} />}
        />
      </AuthDataProvider>
    </QueryClientProvider>,
    { route: `/election/1/${view}` }
  )

describe('AA setup flow', () => {
  const setupApiCalls = [
    aaApiCalls.getJurisdictions,
    aaApiCalls.getContests,
    aaApiCalls.getSettings(auditSettings.all),
  ]

  it('sidebar changes stages', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText, getByText } = render()

      await waitFor(() => {
        expect(queryAllByText('Participants')).toHaveLength(2)
      })

      fireEvent.click(getByText('Audit Settings') as Element, { bubbles: true })

      await waitFor(() => {
        expect(queryAllByText('Audit Settings')).toHaveLength(2)
      })
    })
  })

  it('renders sidebar when authenticated on /setup', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container, queryAllByText } = render()

      await waitFor(() => {
        expect(queryAllByText('Participants')).toHaveLength(2)
      })
      expect(container).toMatchSnapshot()
    })
  })

  it('get empty jurisdiction file initially', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText } = render()

      await waitFor(() => {
        expect(queryAllByText('Participants')).toHaveLength(2)
        screen.getByLabelText('Select a file...')
      })
    })
  })

  it('get jurisdiction file if exists', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryByText, queryAllByText } = render()

      await waitFor(() => {
        expect(queryAllByText('Participants')).toHaveLength(2)
        expect(queryByText(/Current file/))
      })
    })
  })

  it('jurisdiction file upload success', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
      aaApiCalls.putJurisdictionFile,
      aaApiCalls.getJurisdictionFileWithResponse(
        jurisdictionFileMocks.processed
      ),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFileWithResponse(
        jurisdictionFileMocks.processed
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText } = render()

      await waitFor(() => {
        expect(queryAllByText('Participants')).toHaveLength(2)
      })
      const jurisdisctionInput = screen.getByLabelText('Select a file...')
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

  it('jurisdiction file upload with error', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
      aaApiCalls.putJurisdictionErrorFile,
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText } = render()

      await waitFor(() => {
        expect(queryAllByText('Participants')).toHaveLength(2)
      })
      const jurisdisctionInput = screen.getByLabelText('Select a file...')
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
    const ballotComparisonSetupApiCalls = [
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings(auditSettings.ballotComparisonAll),
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...ballotComparisonSetupApiCalls,
      aaApiCalls.getSettings(auditSettings.ballotComparisonAll),
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.empty
      ),
      aaApiCalls.putStandardizedContestsFile,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.processed
      ),
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.processed
      ),
      ...ballotComparisonSetupApiCalls,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.processed
      ),
      aaApiCalls.getSettings(auditSettings.ballotComparisonAll),
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.processed
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()

      // check file upload of jurisdiction
      await screen.findByText(/Uploaded/)
      const standardizedContestInput = screen.getByLabelText('Select a file...')
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
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds(roundMocks.singleIncomplete),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = render('')
      await waitFor(() => {
        expect(history.location.pathname).toEqual('/election/1/progress')
      })
    })
  })

  it('shows an error and undo button if drawing the sample fails', async () => {
    const afterLaunchApiCalls = [
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests,
      aaApiCalls.getSettings(auditSettings.all),
      aaApiCalls.getSettings(auditSettings.all),
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds(roundMocks.drawSampleErrored),
      ...afterLaunchApiCalls,
      aaApiCalls.getJurisdictionFile,
      ...afterLaunchApiCalls,
      aaApiCalls.getJurisdictionFile,
      {
        url: '/api/election/1/round/round-1',
        options: { method: 'DELETE' },
        response: { status: 'ok' },
      },
      aaApiCalls.getRounds(roundMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
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

  it('reloads jurisdiction progress after file upload', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      ...setupApiCalls,
      aaApiCalls.getMapData,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      jaApiCalls.putManifest,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      {
        ...aaApiCalls.getJurisdictions,
        response: { jurisdictions: jurisdictionMocks.allManifests },
      },
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render('progress')

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      screen.getByText('Audit Progress')
      let rows = screen.getAllByRole('row')
      let row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction One')
      within(row1[1]).getByText('No manifest uploaded')

      // Click on a jurisdiction name to open the detail modal
      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction One' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction One' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText('Ballot Manifest')

      // Upload a manifest
      userEvent.upload(
        within(modal).getByLabelText('Select a file...'),
        manifestFile
      )
      await within(modal).findByText('manifest.csv')
      userEvent.click(within(modal).getByRole('button', { name: /Upload/ }))
      await within(modal).findByText('Uploaded')

      // Close the detail modal
      userEvent.click(screen.getByRole('button', { name: 'Close' }))

      // Jurisdiction table should be updated
      rows = screen.getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      within(row1[1]).getByText('Manifest uploaded')
    })
  })
})

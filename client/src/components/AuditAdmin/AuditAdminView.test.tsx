import React from 'react'
import { waitFor, fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, RouteProps } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import AuditAdminView from './AuditAdminView'
import {
  withMockFetch,
  renderWithRouter,
  createQueryClient,
} from '../testUtilities'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'
import {
  aaApiCalls,
  jaApiCalls,
  jurisdictionFileMocks,
  standardizedContestsFileMocks,
  auditSettingsMocks,
  roundMocks,
  manifestFile,
  manifestMocks,
  jurisdictionMocks,
  contestMocks,
} from '../_mocks'
import {
  jurisdictionFile,
  standardizedContestsFile,
} from './Setup/Participants/_mocks'
import { sampleSizeMock } from './Setup/Review/_mocks'

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
    aaApiCalls.getRounds([]),
    aaApiCalls.getJurisdictions,
    aaApiCalls.getContests(contestMocks.filledTargeted),
    aaApiCalls.getSettings(auditSettingsMocks.all),
    aaApiCalls.getJurisdictionFile,
  ]

  it('sidebar changes stages', async () => {
    const expectedCalls = [aaApiCalls.getUser, ...setupApiCalls]
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
    const expectedCalls = [aaApiCalls.getUser, ...setupApiCalls]
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
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
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
    const expectedCalls = [aaApiCalls.getUser, ...setupApiCalls]
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
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
      aaApiCalls.uploadJurisdictionFileGetUrl,
      aaApiCalls.uploadJurisdictionFilePostFile,
      aaApiCalls.uploadJurisdictionFileUploadComplete,
      aaApiCalls.getJurisdictionFileWithResponse(
        jurisdictionFileMocks.processed
      ),
      aaApiCalls.getJurisdictions,
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
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
      aaApiCalls.uploadJurisdictionFileGetUrl,
      aaApiCalls.uploadJurisdictionFilePostFile,
      aaApiCalls.uploadJurisdictionFileUploadCompleteError,
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.errored),
      aaApiCalls.getJurisdictions,
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
      await screen.findByText('Invalid CSV')
    })
  })

  it('standardized contests file upload success', async () => {
    const ballotComparisonSetupApiCalls = [
      aaApiCalls.getRounds([]),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
      aaApiCalls.getJurisdictionFile,
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      ...ballotComparisonSetupApiCalls,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.empty
      ),
      aaApiCalls.uploadStandardizedContestsFileGetUrl,
      aaApiCalls.uploadStandardizedContestsFilePostFile,
      aaApiCalls.uploadStandardizedContestsFileUploadComplete,
      aaApiCalls.getStandardizedContestsFileWithResponse(
        standardizedContestsFileMocks.processed
      ),
      aaApiCalls.getContests(contestMocks.filledTargeted),
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

  it('shows a spinner while sample is being drawn', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds(roundMocks.drawSampleInProgress),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
    ]
    await withMockFetch(expectedCalls, async () => {
      render('progress')
      await screen.findByRole('heading', {
        name: 'Drawing a random sample of ballots...',
      })
      screen.getByText(
        'For large elections, this can take a couple of minutes.'
      )
    })
  })

  it('redirects to /progress after audit is launched', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      ...setupApiCalls,
      aaApiCalls.getStandardizedContests([]),
      aaApiCalls.getContestChoiceNameStandardizations(),
      aaApiCalls.getSampleSizes(sampleSizeMock.ballotPolling),
      aaApiCalls.postRound({
        'contest-id': sampleSizeMock.ballotPolling.sampleSizes![
          'contest-id'
        ][0],
      }),
      aaApiCalls.getRounds(roundMocks.singleIncomplete),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getLastLoginByJurisdiction(),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = render('setup')
      await screen.findByRole('heading', { name: 'Audit Setup' })
      userEvent.click(screen.getByRole('link', { name: 'Review & Launch' }))
      await screen.findByRole('heading', { name: 'Review & Launch' })
      userEvent.click(screen.getByRole('button', { name: 'Launch Audit' }))
      const dialog = (
        await screen.findByRole('heading', {
          name: 'Are you sure you want to launch the audit?',
        })
      ).closest('div.bp3-dialog') as HTMLElement
      userEvent.click(
        within(dialog).getByRole('button', { name: 'Launch Audit' })
      )

      await screen.findByRole('heading', { name: 'Audit Progress' })
      expect(history.location.pathname).toEqual('/election/1/progress')
    })
  })

  it('shows an error and undo button if drawing the sample fails', async () => {
    const afterLaunchApiCalls = [
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
    ]
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds(roundMocks.drawSampleErrored),
      ...afterLaunchApiCalls,
      {
        url: '/api/election/1/round/current',
        options: { method: 'DELETE' },
        response: { status: 'ok' },
      },
      aaApiCalls.getJurisdictions,
      aaApiCalls.getRounds(roundMocks.empty),
      aaApiCalls.getLastLoginByJurisdiction(),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { history } = render('progress')
      await screen.findByRole('heading', {
        name: 'Arlo could not draw the sample',
      })
      screen.getByText(
        'Please contact our support team for help resolving this issue.'
      )
      screen.getByText('Error: something went wrong')
      expect(history.location.pathname).toEqual('/election/1/progress')

      userEvent.click(screen.getByRole('button', { name: 'Undo Audit Launch' }))
      await screen.findByText('The audit has not started.')
    })
  })

  it('reloads jurisdiction progress after file upload', async () => {
    const expectedCalls = [
      aaApiCalls.getUser,
      aaApiCalls.getRounds([]),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getSettings(auditSettingsMocks.all),
      aaApiCalls.getLastLoginByJurisdiction(),
      aaApiCalls.getMapData,
      jaApiCalls.getBallotManifestFile(manifestMocks.empty),
      ...jaApiCalls.uploadManifestCalls,
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      {
        ...aaApiCalls.getJurisdictions,
        response: { jurisdictions: jurisdictionMocks.allManifests },
      },
      aaApiCalls.getLastLoginByJurisdiction(),
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
      within(row1[1]).getByText('Logged in')

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

it('finishes a round', async () => {
  const expectedCalls = [
    aaApiCalls.getUser,
    aaApiCalls.getRounds(roundMocks.singleIncomplete),
    {
      ...aaApiCalls.getJurisdictions,
      response: { jurisdictions: jurisdictionMocks.allComplete },
    },
    aaApiCalls.getContests(contestMocks.filledTargeted),
    aaApiCalls.getSettings(auditSettingsMocks.all),
    aaApiCalls.getLastLoginByJurisdiction(),
    aaApiCalls.getMapData,
    aaApiCalls.postFinishRound,
    aaApiCalls.getRounds(roundMocks.singleComplete),
  ]
  await withMockFetch(expectedCalls, async () => {
    render('progress')
    await screen.findByRole('heading', { name: 'Audit Progress' })
    userEvent.click(screen.getByRole('button', { name: 'Finish Round 1' }))
    await screen.findByText('Congratulations - the audit is complete!')
  })
})

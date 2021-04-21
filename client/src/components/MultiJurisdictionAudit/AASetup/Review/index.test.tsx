import React from 'react'
import userEvent from '@testing-library/user-event'
import { screen, fireEvent, waitFor, within } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import relativeStages from '../_mocks'
import Review from './index'
import * as utilities from '../../../utilities'
import { settingsMock, sampleSizeMock } from './_mocks'
import { contestMocks } from '../Contests/_mocks'
import {
  jurisdictionMocks,
  fileProcessingMocks,
  auditSettings,
} from '../../useSetupMenuItems/_mocks'
import { withMockFetch, renderWithRouter } from '../../../testUtilities'
import { IJurisdiction } from '../../useJurisdictions'
import { IContest } from '../../../../types'
import { IAuditSettings } from '../../useAuditSettings'
import { ISampleSizesResponse } from './useSampleSizes'
import { FileProcessingStatus } from '../../useCSV'
import { IContestNameStandardizations } from '../../useContestNameStandardizations'

const apiCalls = {
  getSettings: (response: IAuditSettings) => ({
    url: '/api/election/1/settings',
    response,
  }),
  getSampleSizeOptions: (response: ISampleSizesResponse) => ({
    url: '/api/election/1/sample-sizes',
    response,
  }),
  getRounds: {
    url: '/api/election/1/round',
    response: { rounds: [] },
  },
  postRound: (sampleSizes: { [contestId: string]: number }) => ({
    url: '/api/election/1/round',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify({
        roundNum: 1,
        sampleSizes,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
    },
  }),
  getJurisdictions: (response: { jurisdictions: IJurisdiction[] }) => ({
    url: '/api/election/1/jurisdiction',
    response,
  }),
  getJurisdictionFile: {
    url: '/api/election/1/jurisdiction/file',
    response: {
      file: { name: 'jurisdictions.csv' },
      processing: fileProcessingMocks.processed,
    },
  },
  getStandardizedContestsFile: {
    url: '/api/election/1/standardized-contests/file',
    response: {
      file: { name: 'standardized-contests.csv' },
      processing: fileProcessingMocks.processed,
    },
  },
  getContests: (response: { contests: IContest[] }) => ({
    url: '/api/election/1/contest',
    response,
  }),
  getStandardizations: (response: IContestNameStandardizations) => ({
    url: '/api/election/1/contest/standardizations',
    response,
  }),
  putStandardizations: (
    standardizations: IContestNameStandardizations['standardizations']
  ) => ({
    url: '/api/election/1/contest/standardizations',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify(standardizations),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'PUT',
    },
  }),
}

const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: jest.fn(),
}))
const routeMock = useParams as jest.Mock
routeMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

const { prevStage } = relativeStages('review')

const refreshMock = jest.fn()
const startNextRoundMock = jest.fn().mockResolvedValue(true)

const renderView = (props = {}) =>
  renderWithRouter(
    <Review
      locked={false}
      prevStage={prevStage}
      refresh={refreshMock}
      startNextRound={startNextRoundMock}
      {...props}
    />,
    {
      route: '/election/1/setup',
    }
  )

beforeEach(() => {
  refreshMock.mockClear()
  startNextRoundMock.mockClear()
  toastSpy.mockClear()
  checkAndToastMock.mockClear()
  routeMock.mockClear()
  ;(prevStage.activate as jest.Mock).mockClear()
})

describe('Audit Setup > Review & Launch', () => {
  it('renders empty state', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state with offline setting', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.offline),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state with batch comparison and no tallies files uploaded', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.batch),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('View jurisdiction upload progress.')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state with batch comparison and all tallies files uploaded', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.batch),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsAllTallies,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText(
        'Choose the initial sample size for each contest you would like to use for Round 1 of the audit from the options below.'
      )
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state with jurisdictions with targeted and opportunistic contests', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedAndOpportunistic),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('shows the contest settings', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedAndOpportunistic),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')

      screen.getByRole('heading', { name: 'Contests' })

      const contest1 = screen
        .getAllByRole('heading', { name: 'Contest 1' })[0]
        .closest('div.bp3-card') as HTMLElement

      // Contest settings
      within(contest1).getByText('Target Contest')
      within(contest1).getByText(
        '1 winner - 1 vote allowed - 30 total ballots cast'
      )

      // Choice vote counts table
      const choices = within(contest1)
        .getByRole('columnheader', {
          name: 'Choice',
        })
        .closest('table')!
      within(choices).getByRole('columnheader', { name: 'Votes' })
      const choiceRows = within(choices).getAllByRole('row')
      within(choiceRows[1]).getByRole('cell', { name: 'Choice One' })
      within(choiceRows[1]).getByRole('cell', { name: '10' })
      within(choiceRows[2]).getByRole('cell', { name: 'Choice Two' })
      within(choiceRows[2]).getByRole('cell', { name: '20' })

      // Contest universe
      const universe = within(contest1)
        .getByRole('columnheader', {
          name: 'Contest universe: 2/3\xa0jurisdictions',
        })
        .closest('table')!
      const universeRows = within(universe).getAllByRole('row')
      expect(universeRows.length).toEqual(2 + 1) // Includes headers
      within(universeRows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
      within(universeRows[2]).getByRole('cell', { name: 'Jurisdiction 2' })

      const contest2 = screen
        .getAllByRole('heading', { name: 'Contest 2' })[0]
        .closest('div.bp3-card') as HTMLElement

      // Contest settings
      within(contest2).getByText('Opportunistic Contest')
      within(contest2).getByText(
        '2 winners - 2 votes allowed - 300,000 total ballots cast'
      )
    })
  })

  it('for hybrid audits, shows the CVR/non-CVR vote totals and sample sizes', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.hybridAll),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsWithCVRs,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedAndOpportunistic),
      apiCalls.getStandardizedContestsFile,
      apiCalls.getStandardizations({
        standardizations: {},
        cvrContestNames: {},
      }),
      apiCalls.getSampleSizeOptions({
        ...sampleSizeMock,
        sampleSizes: {
          'contest-id': [
            { key: 'suite', size: 10, sizeCvr: 3, sizeNonCvr: 7, prob: null },
          ],
        },
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')

      // Vote totals in contest section
      const contest1 = screen
        .getAllByRole('heading', { name: 'Contest 1' })[0]
        .closest('div.bp3-card') as HTMLElement

      const choices = within(contest1)
        .getByRole('columnheader', {
          name: 'Choice',
        })
        .closest('table')!
      within(choices).getByRole('columnheader', { name: 'Votes' })
      within(choices).getByRole('columnheader', { name: 'CVR' })
      within(choices).getByRole('columnheader', { name: 'Non-CVR' })
      const choiceRows = within(choices).getAllByRole('row')
      within(choiceRows[1]).getByRole('cell', { name: 'Choice One' })
      within(choiceRows[1]).getByRole('cell', { name: '10' })
      within(choiceRows[1]).getByRole('cell', { name: '6' })
      within(choiceRows[1]).getByRole('cell', { name: '4' })
      within(choiceRows[2]).getByRole('cell', { name: 'Choice Two' })
      within(choiceRows[2]).getByRole('cell', { name: '20' })
      within(choiceRows[2]).getByRole('cell', { name: '12' })
      within(choiceRows[2]).getByRole('cell', { name: '8' })

      // Sample sizes
      const options = screen.getAllByRole('radio')
      expect(options).toHaveLength(1)
      expect(options[0].closest('label')).toHaveTextContent(
        '10 samples (3 CVR ballots and 7 non-CVR ballots)'
      )
    })
  })

  it('for hybrid audits, doesnt show the CVR/non-CVR vote totals when sample sizes errors', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.hybridAll),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsWithCVRs,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargeted),
      apiCalls.getStandardizedContestsFile,
      apiCalls.getStandardizations({
        standardizations: {},
        cvrContestNames: {},
      }),
      apiCalls.getSampleSizeOptions({
        ...sampleSizeMock,
        sampleSizes: null,
        task: {
          ...sampleSizeMock.task,
          status: FileProcessingStatus.ERRORED,
          error: 'sample sizes error',
        },
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')

      const contest1 = screen
        .getAllByRole('heading', { name: 'Contest Name' })[0]
        .closest('div.bp3-card') as HTMLElement
      const choices = within(contest1)
        .getByRole('columnheader', {
          name: 'Choice',
        })
        .closest('table')!
      within(choices).getByRole('columnheader', { name: 'Votes' })
      within(choices).getByRole('columnheader', { name: 'CVR' })
      within(choices).getByRole('columnheader', { name: 'Non-CVR' })
      const choiceRows = within(choices).getAllByRole('row')
      expect(
        within(choiceRows[1])
          .getAllByRole('cell')
          .map(cell => cell.textContent)
      ).toEqual(['Choice One', '10', '', ''])

      // Check that the error from the sample size endpoint is shown
      screen.getByRole('heading', { name: 'Sample Size' })
      screen.getByText('sample sizes error')
    })
  })

  it('when CVRs arent all uploaded for ballot comparison audits, hides contest settings and sample sizes', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.ballotComparisonAll),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsSomeCVRs,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedAndOpportunistic),
      apiCalls.getStandardizedContestsFile,
      apiCalls.getStandardizations({
        standardizations: {},
        cvrContestNames: {},
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')

      screen.getByRole('heading', { name: 'Contests' })
      const contest1 = screen
        .getAllByRole('heading', { name: 'Contest 1' })[0]
        .closest('div.bp3-card') as HTMLElement
      within(contest1).getByText(
        'Waiting for all jurisdictions to upload CVRs to compute contest settings.'
      )

      screen.getByRole('heading', { name: 'Sample Size' })
      screen.getByText(
        'All jurisdiction files must be uploaded and all audit settings' +
          ' must be configured in order to calculate the sample size.'
      )
      expect(
        screen.getByRole('link', { name: 'View jurisdiction upload progress.' })
      ).toHaveAttribute('href', '/election/1/progress')
    })
  })

  it('launches the first round', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')
      const launchButton = screen.getByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton)
      await waitFor(() => {
        expect(startNextRoundMock).toHaveBeenCalledWith({
          'contest-id': { key: 'asn', size: 46, prob: 0.54 },
        })
        expect(refreshMock).toHaveBeenCalled()
      })
    })
  })

  it('cancels audit launch', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')
      const launchButton = screen.getByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const cancelLaunchButton = screen.getByText('Cancel')
      userEvent.click(cancelLaunchButton)
      await waitFor(() =>
        expect(
          screen.queryByText('Are you sure you want to launch the audit?')
        ).not.toBeInTheDocument()
      )
    })
  })

  it('launches the first round with a non-default sample size', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      const newSampleSize = await screen.findByText(
        '67 samples (70% chance of reaching risk limit and completing the audit in one round)'
      )
      userEvent.click(newSampleSize)
      const launchButton = await screen.findByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton)
      await waitFor(() => {
        expect(startNextRoundMock).toHaveBeenCalledWith({
          'contest-id': { key: '0.7', size: 67, prob: 0.7 },
        })
        expect(refreshMock).toHaveBeenCalled()
      })
    })
  })

  it('accepts custom sample size', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      const newSampleSize = await screen.findByText(
        'Enter your own sample size (not recommended)'
      )
      userEvent.click(newSampleSize)
      const customSampleSizeInput = await screen.findByRole('spinbutton')
      fireEvent.change(customSampleSizeInput, { target: { value: '40' } }) // userEvent has a problem with this field due to the lack of an explicit value field: https://github.com/testing-library/user-event/issues/356
      fireEvent.blur(customSampleSizeInput)
      await screen.findByText(
        'Must be less than or equal to: 30 (the total number of ballots in the contest)'
      )
      userEvent.clear(customSampleSizeInput)
      fireEvent.change(customSampleSizeInput, { target: { value: '5' } })
      await waitFor(() =>
        expect(
          screen.queryByText(
            'Must be less than or equal to: 30 (the total number of ballots in the contest)'
          )
        ).toBeNull()
      )
      const launchButton = await screen.findByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton)
      await waitFor(() => {
        expect(startNextRoundMock).toHaveBeenCalledWith({
          'contest-id': { key: 'custom', size: 5, prob: null },
        })
        expect(refreshMock).toHaveBeenCalled()
      })
    })
  })

  it('has links to download jurisdictions and standardized contests file', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.ballotComparisonAll),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getStandardizedContestsFile,
      apiCalls.getStandardizations({
        standardizations: {},
        cvrContestNames: {},
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      const jurisdictionsFileLink = await screen.findByRole('link', {
        name: 'jurisdictions.csv',
      })
      expect(jurisdictionsFileLink).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/file/csv'
      )
      const standardizedContestsFileLink = await screen.findByRole('link', {
        name: 'standardized-contests.csv',
      })
      expect(standardizedContestsFileLink).toHaveAttribute(
        'href',
        '/api/election/1/standardized-contests/file/csv'
      )
    })
  })

  it('custom sample size validation - batch comparison', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.batch),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsAllTallies,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText(
        'Choose the initial sample size for each contest you would like to use for Round 1 of the audit from the options below.'
      )
      expect(container).toMatchSnapshot()
      const newSampleSize = await screen.findByText(
        'Enter your own sample size (not recommended)'
      )
      userEvent.click(newSampleSize)
      const customSampleSizeInput = await screen.findByRole('spinbutton')
      fireEvent.change(customSampleSizeInput, { target: { value: '40' } }) // userEvent has a problem with this field due to the lack of an explicit value field: https://github.com/testing-library/user-event/issues/356
      fireEvent.blur(customSampleSizeInput)
      await screen.findByText(
        'Must be less than or equal to: 20 (the total number of batches in the contest)'
      )
    })
  })

  it('custom sample size validation - ballot comparison', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.ballotComparisonAll),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsWithCVRs,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getStandardizedContestsFile,
      apiCalls.getStandardizations({
        standardizations: {},
        cvrContestNames: {},
      }),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText(
        'Choose the initial sample size for each contest you would like to use for Round 1 of the audit from the options below.'
      )
      expect(container).toMatchSnapshot()
      const newSampleSize = await screen.findByText(
        'Enter your own sample size (not recommended)'
      )
      userEvent.click(newSampleSize)
      const customSampleSizeInput = await screen.findByRole('spinbutton')
      fireEvent.change(customSampleSizeInput, { target: { value: '50' } }) // userEvent has a problem with this field due to the lack of an explicit value field: https://github.com/testing-library/user-event/issues/356
      fireEvent.blur(customSampleSizeInput)
      await screen.findByText(
        'Must be less than or equal to: 30 (the total number of ballots in the contest)'
      )
    })
  })

  it('shows the selected sample size after launch', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifests,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
      apiCalls.getSampleSizeOptions({
        ...sampleSizeMock,
        selected: { 'contest-id': { key: 'custom', size: 100, prob: null } },
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({ locked: true })
      await screen.findByText(/Choose the initial sample size/)
      // All the options should still be showing
      const options = screen.getAllByRole('radio')
      expect(options).toHaveLength(5)
      options.forEach(option => expect(option).toBeDisabled())
      expect(options[0].closest('label')).toHaveTextContent(
        'BRAVO Average Sample Number: 46 samples (54% chance of reaching risk limit and completing the audit in one round)'
      )
      expect(options[1].closest('label')).toHaveTextContent(
        '67 samples (70% chance of reaching risk limit and completing the audit in one round)'
      )
      expect(options[2].closest('label')).toHaveTextContent(
        '88 samples (50% chance of reaching risk limit and completing the audit in one round)'
      )
      expect(options[3].closest('label')).toHaveTextContent(
        '125 samples (90% chance of reaching risk limit and completing the audit in one round)'
      )
      expect(options[4].closest('label')).toHaveTextContent(
        'Enter your own sample size (not recommended)'
      )
      // Custom option should be checked and show value
      expect(options[4]).toBeChecked()
      const customSampleSizeInput = screen.getByRole('spinbutton')
      expect(customSampleSizeInput).toHaveValue(100)
      expect(customSampleSizeInput).toBeDisabled()
    })
  })

  it('shows warning and dialog to standardize contest names', async () => {
    const standardizations = {
      'jurisdiction-id-1': {
        'Contest 1': null,
      },
      'jurisdiction-id-2': {
        'Contest 2': null,
      },
    }
    const cvrContestNames = {
      'jurisdiction-id-1': ['Contest One', 'Contest Two'],
      'jurisdiction-id-2': ['Contest One', 'Contest Two'],
    }
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.ballotComparisonAll),
      apiCalls.getJurisdictions({
        jurisdictions: jurisdictionMocks.allManifestsWithCVRs,
      }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedAndOpportunistic),
      apiCalls.getStandardizedContestsFile,
      apiCalls.getStandardizations({
        standardizations,
        cvrContestNames,
      }),
      apiCalls.putStandardizations({
        'jurisdiction-id-1': {
          'Contest 1': 'Contest One',
        },
        'jurisdiction-id-2': {
          'Contest 2': null,
        },
      }),
      apiCalls.getStandardizations({
        standardizations: {
          ...standardizations,
          'jurisdiction-id-1': { 'Contest 1': 'Contest One' },
        },
        cvrContestNames,
      }),
      apiCalls.putStandardizations({
        'jurisdiction-id-1': {
          'Contest 1': 'Contest One',
        },
        'jurisdiction-id-2': {
          'Contest 2': 'Contest Two',
        },
      }),
      apiCalls.getStandardizations({
        standardizations: {
          'jurisdiction-id-1': { 'Contest 1': 'Contest One' },
          'jurisdiction-id-2': { 'Contest 2': 'Contest Two' },
        },
        cvrContestNames,
      }),
      apiCalls.getSampleSizeOptions(sampleSizeMock),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')

      // Sample size should not be fetched
      screen.getByRole('heading', { name: 'Sample Size' })
      screen.getByText(
        'All contest names must be standardized in order to calculate the sample size.'
      )
      expect(
        screen.getByRole('button', { name: 'Launch Audit' })
      ).toBeDisabled()

      // Open the dialog
      screen.getByText(
        'Some contest names in the CVR files do not match the target/opportunistic contest names.'
      )
      userEvent.click(
        screen.getByRole('button', { name: 'Standardize Contest Names' })
      )

      // Should show a form
      let dialog = (await screen.findByRole('heading', {
        name: 'Standardize Contest Names',
      })).closest('div.bp3-dialog') as HTMLElement
      expect(
        within(dialog)
          .getAllByRole('columnheader')
          .map(header => header.textContent)
      ).toEqual(['Jurisdiction', 'Target/Opportunistic Contest', 'CVR Contest'])
      let rows = within(dialog).getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
      within(rows[1]).getByRole('cell', { name: 'Contest 1' })
      within(rows[2]).getByRole('cell', { name: 'Jurisdiction 2' })
      within(rows[2]).getByRole('cell', { name: 'Contest 2' })

      // Select a CVR contest name
      const contest1Select = within(rows[1]).getByRole('combobox')
      expect(contest1Select).toHaveValue('')
      userEvent.selectOptions(contest1Select, 'Contest One')

      // Submit the form
      userEvent.click(within(dialog).getByRole('button', { name: 'Submit' }))
      await waitFor(() => expect(dialog).not.toBeInTheDocument())

      // Should still show warning since we didn't finish standardizing
      screen.getByText(
        'Some contest names in the CVR files do not match the target/opportunistic contest names.'
      )

      // Reopen the form - should show the standardization we already did
      userEvent.click(
        screen.getByRole('button', { name: 'Standardize Contest Names' })
      )
      dialog = (await screen.findByRole('heading', {
        name: 'Standardize Contest Names',
      })).closest('div.bp3-dialog') as HTMLElement
      rows = within(dialog).getAllByRole('row')
      expect(within(rows[1]).getByRole('combobox')).toHaveValue('Contest One')

      // Finish standardizing
      userEvent.selectOptions(
        within(rows[2]).getByRole('combobox'),
        'Contest Two'
      )
      userEvent.click(within(dialog).getByRole('button', { name: 'Submit' }))
      await waitFor(() => expect(dialog).not.toBeInTheDocument())

      // Warning is gone, sample sizes are shown
      screen.getByText(
        'All contest names in the CVR files have been standardized to match the target/opportunistic contest names.'
      )
      screen.getByText(
        'Choose the initial sample size for each contest you would like to use for Round 1 of the audit from the options below.'
      )

      // Can still open dialog to edit
      userEvent.click(
        screen.getByRole('button', { name: 'Edit Standardized Contest Names' })
      )
      dialog = (await screen.findByRole('heading', {
        name: 'Standardize Contest Names',
      })).closest('div.bp3-dialog') as HTMLElement
      userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
      await waitFor(() => expect(dialog).not.toBeInTheDocument())
    })
  })
})

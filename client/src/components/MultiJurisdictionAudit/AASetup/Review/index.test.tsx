import React from 'react'
import userEvent from '@testing-library/user-event'
import { screen, fireEvent, waitFor } from '@testing-library/react'
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
import { ISampleSizes } from './useSampleSizes'
import { IJurisdiction } from '../../useJurisdictions'
import { IContest } from '../../../../types'
import { IAuditSettings } from '../../useAuditSettings'

const apiCalls = {
  getSettings: (response: IAuditSettings) => ({
    url: '/api/election/1/settings',
    response,
  }),
  getSampleSizeOptions: {
    url: '/api/election/1/sample-sizes',
    response: sampleSizeMock,
  },
  postRound: (sampleSizes: ISampleSizes) => ({
    url: '/api/election/1/round',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify({
        sampleSizes,
        roundNum: 1,
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

const renderView = () =>
  renderWithRouter(
    <Review locked={false} prevStage={prevStage} refresh={refreshMock} />,
    {
      route: '/election/1/setup',
    }
  )

beforeEach(() => {
  refreshMock.mockClear()
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
      apiCalls.getSampleSizeOptions,
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
      apiCalls.getSampleSizeOptions,
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
      apiCalls.getSampleSizeOptions,
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
      apiCalls.getSampleSizeOptions,
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
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders despite missing jurisdictions on targeted contest', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({ jurisdictions: [] }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledTargetedWithJurisdictionId),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders despite missing jurisdictions on opportunistic contest', async () => {
    const expectedCalls = [
      apiCalls.getSettings(settingsMock.full),
      apiCalls.getJurisdictions({ jurisdictions: [] }),
      apiCalls.getJurisdictionFile,
      apiCalls.getContests(contestMocks.filledOpportunisticWithJurisdictionId),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
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
      apiCalls.getSampleSizeOptions,
      apiCalls.postRound({ 'contest-id': 46 }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')
      const launchButton = screen.getByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton)
      await waitFor(() => expect(refreshMock).toHaveBeenCalled())
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
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      await screen.findByText('Review & Launch')
      const launchButton = screen.getByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const cancelLaunchButton = screen.getByText('Cancel')
      userEvent.click(cancelLaunchButton)
      await waitFor(() => expect(refreshMock).not.toHaveBeenCalled())
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
      apiCalls.getSampleSizeOptions,
      apiCalls.postRound({ 'contest-id': 67 }),
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
      await waitFor(() => expect(refreshMock).toHaveBeenCalled())
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
      apiCalls.getSampleSizeOptions,
      apiCalls.postRound({ 'contest-id': 5 }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView()
      const newSampleSize = await screen.findByText(
        'Enter your own sample size (not recommended)'
      )
      userEvent.click(newSampleSize)
      const customSampleSizeInput = await screen.findByRole('textbox')
      fireEvent.change(customSampleSizeInput, { target: { value: '40' } }) // userEvent has a problem with this field due to the lack of an explicit value field: https://github.com/testing-library/user-event/issues/356
      fireEvent.blur(customSampleSizeInput)
      await screen.findByText(
        'Must be less than or equal to: 30 (the total number of ballots in this targeted contest)'
      )
      userEvent.clear(customSampleSizeInput)
      fireEvent.change(customSampleSizeInput, { target: { value: '5' } })
      await waitFor(() =>
        expect(
          screen.queryByText(
            'Must be less than or equal to: 30 (the total number of ballots in this targeted contest)'
          )
        ).toBeNull()
      )
      const launchButton = await screen.findByText('Launch Audit')
      userEvent.click(launchButton)
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton)
      await waitFor(() => expect(refreshMock).toHaveBeenCalled())
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
})

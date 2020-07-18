import React from 'react'
import userEvent from '@testing-library/user-event'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import relativeStages from '../_mocks'
import Review from './index'
import * as utilities from '../../../utilities'
import useAuditSettings from '../../useAuditSettings'
import { settingsMock, sampleSizeMock } from './_mocks'
import { contestMocks } from '../Contests/_mocks'
import { jurisdictionMocks } from '../../_mocks'
import { withMockFetch } from '../../../testUtilities'

const auditSettingsMock = useAuditSettings as jest.Mock

const apiCalls = {
  getSampleSizeOptions: {
    url: '/api/election/1/sample-sizes',
    response: sampleSizeMock,
  },
  putDefaultSampleSize: {
    url: '/api/election/1/round',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify({
        sampleSizes: { 'contest-id': 46 },
        roundNum: 1,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
    },
  },
  putNondefaultSampleSize: {
    url: '/api/election/1/round',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify({
        sampleSizes: { 'contest-id': 67 },
        roundNum: 1,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
    },
  },
  putCustomSampleSize: {
    url: '/api/election/1/round',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify({
        sampleSizes: { 'contest-id': 5 },
        roundNum: 1,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
    },
  },
  getEmptyJurisdictions: {
    url: '/api/election/1/jurisdiction',
    response: { jurisdictions: [] },
  },
  getJurisdictions: {
    url: '/api/election/1/jurisdiction',
    response: { jurisdictions: jurisdictionMocks.allManifests },
  },
  getJurisdictionFile: {
    url: '/api/election/1/jurisdiction/file',
    response: { file: null, processing: { status: 'PROCESSED' } },
  },
  getTargetedContests: {
    url: '/api/election/1/contest',
    response: contestMocks.filledTargetedWithJurisdictionId,
  },
  getOpportunisticContests: {
    url: '/api/election/1/contest',
    response: contestMocks.filledOpportunisticWithJurisdictionId,
  },
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

jest.mock('../../useAuditSettings')
auditSettingsMock.mockReturnValue(settingsMock.full)

const { prevStage } = relativeStages('Review & Launch')

const refreshMock = jest.fn()

beforeEach(() => {
  refreshMock.mockClear()
  toastSpy.mockClear()
  checkAndToastMock.mockClear()
  routeMock.mockClear()
  ;(prevStage.activate as jest.Mock).mockClear()
  auditSettingsMock.mockClear()
})

describe('Audit Setup > Review & Launch', () => {
  it('renders empty state', async () => {
    const expectedCalls = [
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getTargetedContests,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getTargetedContests,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders full state with jurisdictions on opportunistic contest', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getOpportunisticContests,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders despite missing jurisdictions on targeted contest', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getEmptyJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getTargetedContests,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders despite missing jurisdictions on opportunistic contest', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getEmptyJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getOpportunisticContests,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      await screen.findByText('Review & Launch')
      expect(container).toMatchSnapshot()
    })
  })

  it('launches the first round', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getTargetedContests,
      apiCalls.getSampleSizeOptions,
      apiCalls.putDefaultSampleSize,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      await screen.findByText('Review & Launch')
      const launchButton = screen.getByText('Launch Audit')
      userEvent.click(launchButton, { bubbles: true })
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton, { bubbles: true })
      await waitFor(() => expect(refreshMock).toHaveBeenCalled())
    })
  })

  it.skip('launches the first round with a non-default sample size', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getTargetedContests,
      apiCalls.getSampleSizeOptions,
      apiCalls.putNondefaultSampleSize,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      const newSampleSize = await screen.findByText(
        '67 samples (70% chance of reaching risk limit and completing the audit in one round)'
      )
      userEvent.click(newSampleSize, { bubbles: true })
      const launchButton = await screen.findByText('Launch Audit')
      userEvent.click(launchButton, { bubbles: true })
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton, { bubbles: true })
      await waitFor(() => expect(refreshMock).toHaveBeenCalled())
    })
  })

  it('accepts custom sample size', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const expectedCalls = [
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getTargetedContests,
      apiCalls.getSampleSizeOptions,
      apiCalls.putCustomSampleSize,
      apiCalls.getSampleSizeOptions,
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <Router>
          <Review locked={false} prevStage={prevStage} refresh={refreshMock} />
        </Router>
      )
      const newSampleSize = await screen.findByText(
        'Enter your own sample size (not recommended)'
      )
      userEvent.click(newSampleSize, { bubbles: true })
      const customSampleSizeInput = await screen.findByRole('textbox')
      userEvent.type(customSampleSizeInput, '40')
      fireEvent.blur(customSampleSizeInput)
      await screen.findByText(
        'Must be less than or equal to: 30 (the total number of ballots in this targeted contest)'
      )
      userEvent.clear(customSampleSizeInput)
      fireEvent.blur(customSampleSizeInput)
      userEvent.type(customSampleSizeInput, '5')
      fireEvent.blur(customSampleSizeInput)
      await waitFor(() =>
        expect(
          screen.queryByText(
            'Must be less than or equal to: 30 (the total number of ballots in this targeted contest)'
          )
        ).toBeNull()
      )
      const launchButton = await screen.findByText('Launch Audit')
      userEvent.click(launchButton, { bubbles: true })
      await screen.findByText('Are you sure you want to launch the audit?')
      const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
      userEvent.click(confirmLaunchButton, { bubbles: true })
      // evidently this is calling handleSubmit on line 293, but onSubmit on line 198 is not getting called.
      // The error text is vanishing (I think), so it should be passing validation, but that's the only thing that I know of to block submission.
      await waitFor(() => expect(refreshMock).toHaveBeenCalled())
    })
  })
})

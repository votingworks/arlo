import React from 'react'
import { fireEvent, waitFor, render, screen } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import relativeStages from '../_mocks'
import Review from './index'
import * as utilities from '../../../utilities'
import useAuditSettings from '../../useAuditSettings'
import { settingsMock, sampleSizeMock } from './_mocks'
import { IJurisdiction } from '../../useJurisdictions'
import { contestMocks } from '../Contests/_mocks'
import { ISampleSizeOption, IContest } from '../../../../types'
import { jurisdictionMocks } from '../../_mocks'

const auditSettingsMock = useAuditSettings as jest.Mock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const generateApiMock = (
  sampleSizeReturn: { sampleSizes: ISampleSizeOption[] },
  contestsReturn: { contests: IContest[] } | Error | { status: 'ok' },
  jurisdictionReturn:
    | { jurisdictions: IJurisdiction[] }
    | Error
    | { status: 'ok' }
) => async (endpoint: string) => {
  switch (endpoint) {
    case '/election/1/sample-sizes':
      return sampleSizeReturn
    case '/election/1/jurisdiction':
      return jurisdictionReturn
    case '/election/1/jurisdiction/file':
      return { file: null, processing: { status: 'PROCESSED' } }
    case '/election/1/contest':
      return contestsReturn
    case '/election/1/round':
    default:
      return { status: 'ok' }
  }
}
apiMock.mockImplementation(
  generateApiMock(
    sampleSizeMock,
    contestMocks.filledTargetedWithJurisdictionId,
    { jurisdictions: jurisdictionMocks.allManifests }
  )
)

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

beforeEach(() => {
  apiMock.mockClear()
  toastSpy.mockClear()
  checkAndToastMock.mockClear()
  routeMock.mockClear()
  ;(prevStage.activate as jest.Mock).mockClear()
  auditSettingsMock.mockClear()
})

describe('Audit Setup > Review & Launch', () => {
  it('renders empty state', async () => {
    const { container } = render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders full state', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders full state with jurisdictions on targeted contest', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledTargetedWithJurisdictionId,
        { jurisdictions: jurisdictionMocks.allManifests }
      )
    )
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders full state with jurisdictions on opportunistic contest', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledOpportunisticWithJurisdictionId,
        { jurisdictions: jurisdictionMocks.allManifests }
      )
    )
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders despite missing jurisdictions on targeted contest', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledTargetedWithJurisdictionId,
        {
          jurisdictions: [],
        }
      )
    )
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders despite missing jurisdictions on opportunistic contest', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledOpportunisticWithJurisdictionId,
        {
          jurisdictions: [],
        }
      )
    )
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('launches the first round', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledTargetedWithJurisdictionId,
        { jurisdictions: jurisdictionMocks.allManifests }
      )
    )
    render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    const launchButton = await screen.findByText('Launch Audit')
    fireEvent.click(launchButton, { bubbles: true })
    await screen.findByText('Are you sure you want to launch the audit?')
    const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
    fireEvent.click(confirmLaunchButton, { bubbles: true })
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(5)
      expect(apiMock.mock.calls[4][1]).toMatchObject({
        body: JSON.stringify({
          sampleSize: 46,
          roundNum: 1,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
        method: 'POST',
      })
    })
  })

  it('launches the first round with a non-default sample size', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledTargetedWithJurisdictionId,
        { jurisdictions: jurisdictionMocks.allManifests }
      )
    )
    render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    const newSampleSize = await screen.findByText(
      '67 samples (70% chance of reaching risk limit and completing the audit in one round)'
    )
    fireEvent.click(newSampleSize, { bubbles: true })
    const launchButton = screen.getByText('Launch Audit')
    fireEvent.click(launchButton, { bubbles: true })
    await screen.findByText('Are you sure you want to launch the audit?')
    const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
    fireEvent.click(confirmLaunchButton, { bubbles: true })
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(5)
      expect(apiMock.mock.calls[4][1]).toMatchObject({
        body: JSON.stringify({
          sampleSize: 67,
          roundNum: 1,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
        method: 'POST',
      })
    })
  })

  it('accepts custom sample size', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledTargetedWithJurisdictionId,
        { jurisdictions: jurisdictionMocks.allManifests }
      )
    )
    render(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    const newSampleSize = await screen.findByText(
      'Enter your own sample size (not recommended)'
    )
    fireEvent.click(newSampleSize, { bubbles: true })
    const customSampleSizeInput = await screen.findByRole('textbox')
    fireEvent.change(customSampleSizeInput, { target: { value: '40' } })
    fireEvent.blur(customSampleSizeInput)
    await screen.findByText(
      'Must be less than or equal to the total number of ballots in targeted contests'
    )
    fireEvent.change(customSampleSizeInput, { target: { value: '5' } })
    const launchButton = screen.getByText('Launch Audit')
    fireEvent.click(launchButton, { bubbles: true })
    await screen.findByText('Are you sure you want to launch the audit?')
    const confirmLaunchButton = screen.getAllByText('Launch Audit')[1]
    fireEvent.click(confirmLaunchButton, { bubbles: true })
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(5)
      expect(apiMock.mock.calls[4][1]).toMatchObject({
        body: JSON.stringify({
          sampleSize: 5,
          roundNum: 1,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
        method: 'POST',
      })
    })
  })
})

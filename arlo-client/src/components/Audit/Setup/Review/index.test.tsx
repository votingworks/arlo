import React from 'react'
import { fireEvent, wait } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import relativeStages from '../_mocks'
import Review from './index'
import * as utilities from '../../../utilities'
import { asyncActRender } from '../../../testUtilities'
import useAuditSettings from '../useAuditSettings'
import { settingsMock, sampleSizeMock } from './_mocks'
import { IContests } from '../Contests/types'
import { IJurisdiction } from '../../useJurisdictions'
import { contestMocks } from '../Contests/_mocks'
import { ISampleSizeOption } from '../../../../types'

const auditSettingsMock = useAuditSettings as jest.Mock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const generateApiMock = (
  sampleSizeReturn: { sampleSizes: ISampleSizeOption[] },
  contestsReturn: IContests | Error | { status: 'ok' },
  jurisdictionReturn:
    | { jurisdictions: IJurisdiction[] }
    | Error
    | { status: 'ok' }
) => async (
  endpoint: string
): Promise<
  | IContests
  | { sampleSizes: ISampleSizeOption[] }
  | { jurisdictions: IJurisdiction[] }
  | Error
  | { status: 'ok' }
> => {
  switch (endpoint) {
    case '/election/1/sample-sizes':
      return sampleSizeReturn
    case '/election/1/jurisdiction':
      return jurisdictionReturn
    case '/election/1/contest':
      return contestsReturn
    case '/election/1/round':
    default:
      return { status: 'ok' }
  }
}
apiMock.mockImplementation(
  generateApiMock(sampleSizeMock, contestMocks.filledTargeted, {
    jurisdictions: [],
  })
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

jest.mock('../useAuditSettings')
auditSettingsMock.mockReturnValue(settingsMock.empty)

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
    const { container } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders full state', async () => {
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders full state with jurisdictions on targeted contest', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledTargetedWithJurisdictionId,
        {
          jurisdictions: [
            {
              id: 'jurisdiction-id-1',
              name: 'Jurisdiction One',
              ballotManifest: { file: null, processing: null },
              currentRoundStatus: null,
            },
            {
              id: 'jurisdiction-id-2',
              name: 'Jurisdiction Two',
              ballotManifest: { file: null, processing: null },
              currentRoundStatus: null,
            },
          ],
        }
      )
    )
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders full state with jurisdictions on opportunistic contest', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        sampleSizeMock,
        contestMocks.filledOpportunisticWithJurisdictionId,
        {
          jurisdictions: [
            {
              id: 'jurisdiction-id-1',
              name: 'Jurisdiction One',
              ballotManifest: { file: null, processing: null },
              currentRoundStatus: null,
            },
            {
              id: 'jurisdiction-id-2',
              name: 'Jurisdiction Two',
              ballotManifest: { file: null, processing: null },
              currentRoundStatus: null,
            },
          ],
        }
      )
    )
    auditSettingsMock.mockReturnValue(settingsMock.full)
    const { container } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
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
    const { container } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
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
    const { container } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('launches the first round', async () => {
    apiMock.mockImplementation(
      generateApiMock(sampleSizeMock, contestMocks.filledTargeted, {
        jurisdictions: [],
      })
    )
    const { findByText } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    const launchButton = await findByText('Launch Audit')
    fireEvent.click(launchButton, { bubbles: true })
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(4)
      expect(apiMock.mock.calls[3][1]).toMatchObject({
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
      generateApiMock(sampleSizeMock, contestMocks.filledTargeted, {
        jurisdictions: [],
      })
    )
    const { getByText } = await asyncActRender(
      <Router>
        <Review locked={false} prevStage={prevStage} refresh={jest.fn()} />
      </Router>
    )
    const newSampleSize = getByText(
      '67 samples (70% chance of reaching risk limit and completing the audit in one round)'
    )
    fireEvent.click(newSampleSize, { bubbles: true })
    const launchButton = getByText('Launch Audit')
    fireEvent.click(launchButton, { bubbles: true })
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(4)
      expect(apiMock.mock.calls[3][1]).toMatchObject({
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
})

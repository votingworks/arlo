import React from 'react'
import { useParams } from 'react-router-dom'
import { statusStates, auditSettings } from '../_mocks'
import * as utilities from '../../utilities'
import { asyncActRender } from '../../testUtilities'
import Setup from './index'
import relativeStages from './_mocks'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
apiMock.mockResolvedValue(auditSettings.all)

checkAndToastMock.mockReturnValue(false)

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: jest.fn(),
}))
const routeMock = useParams as jest.Mock
routeMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('Setup', () => {
  it('renders Participants stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates.sampleSizeOptions}
        stage="Participants"
        {...relativeStages('Participants')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Participants"
        {...relativeStages('Participants', 'locked')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Participants"
        {...relativeStages('Participants', 'processing')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates.sampleSizeOptions}
        stage="Target Contests"
        {...relativeStages('Target Contests')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Target Contests"
        {...relativeStages('Target Contests', 'locked')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Target Contests"
        {...relativeStages('Target Contests', 'processing')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates.sampleSizeOptions}
        stage="Opportunistic Contests"
        {...relativeStages('Opportunistic Contests')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Opportunistic Contests"
        {...relativeStages('Opportunistic Contests', 'locked')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Opportunistic Contests"
        {...relativeStages('Opportunistic Contests', 'processing')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates.sampleSizeOptions}
        stage="Audit Settings"
        {...relativeStages('Audit Settings')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Audit Settings"
        {...relativeStages('Audit Settings', 'locked')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Audit Settings"
        {...relativeStages('Audit Settings', 'processing')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates.sampleSizeOptions}
        stage="Review & Launch"
        {...relativeStages('Review & Launch')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Review & Launch"
        {...relativeStages('Review & Launch', 'locked')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        audit={statusStates[2]}
        stage="Review & Launch"
        {...relativeStages('Review & Launch', 'processing')}
      />
    )
    expect(container).toMatchSnapshot()
  })
})

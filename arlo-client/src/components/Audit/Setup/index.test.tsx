import React from 'react'
import { useParams } from 'react-router-dom'
import { auditSettings } from '../_mocks'
import * as utilities from '../../utilities'
import { asyncActRender } from '../../testUtilities'
import Setup from './index'
import relativeStages from './_mocks'
import { contestMocks } from './Contests/_mocks'
import useContests from '../useContests'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
apiMock.mockResolvedValue(auditSettings.all)

const useContestsMock = useContests as jest.Mock
jest.mock('../useContests')
useContestsMock.mockImplementation(() => [
  contestMocks.emptyTargeted,
  jest.fn(),
])

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
        refresh={jest.fn()}
        stage="Participants"
        menuItems={relativeStages('Participants').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Participants"
        menuItems={relativeStages('Participants', 'locked').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Participants"
        menuItems={relativeStages('Participants', 'processing').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Target Contests"
        menuItems={relativeStages('Target Contests').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Target Contests"
        menuItems={relativeStages('Target Contests', 'locked').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Target Contests"
        menuItems={relativeStages('Target Contests', 'processing').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage', async () => {
    useContestsMock.mockImplementation(() => [
      contestMocks.emptyOpportunistic,
      jest.fn(),
    ])
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Opportunistic Contests"
        menuItems={relativeStages('Opportunistic Contests').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage with locked next stage', async () => {
    useContestsMock.mockImplementation(() => [
      contestMocks.emptyOpportunistic,
      jest.fn(),
    ])
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Opportunistic Contests"
        menuItems={relativeStages('Opportunistic Contests', 'locked').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage with processing next stage', async () => {
    useContestsMock.mockImplementation(() => [
      contestMocks.emptyOpportunistic,
      jest.fn(),
    ])
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Opportunistic Contests"
        menuItems={
          relativeStages('Opportunistic Contests', 'processing').menuItems
        }
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Audit Settings"
        menuItems={relativeStages('Audit Settings').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Audit Settings"
        menuItems={relativeStages('Audit Settings', 'locked').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Audit Settings"
        menuItems={relativeStages('Audit Settings', 'processing').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Review & Launch"
        menuItems={relativeStages('Review & Launch').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with locked next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Review & Launch"
        menuItems={relativeStages('Review & Launch', 'locked').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with processing next stage', async () => {
    const { container } = await asyncActRender(
      <Setup
        refresh={jest.fn()}
        stage="Review & Launch"
        menuItems={relativeStages('Review & Launch', 'processing').menuItems}
      />
    )
    expect(container).toMatchSnapshot()
  })
})

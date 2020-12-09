import React from 'react'
import { useParams, MemoryRouter } from 'react-router-dom'
import { render, waitFor, screen } from '@testing-library/react'
import { auditSettings, jurisdictionMocks } from '../useSetupMenuItems/_mocks'
import * as utilities from '../../utilities'
import Setup from './index'
import relativeStages from './_mocks'
import { contestMocks } from './Contests/_mocks'
import useContests from '../useContests'
import useAuditSettings from '../useAuditSettings'
import useJurisdictions from '../useJurisdictions'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
apiMock.mockImplementation(async () => {})

const useJurisdictionsMock = useJurisdictions as jest.Mock
jest.mock('../useJurisdictions')
useJurisdictionsMock.mockImplementation(() => jurisdictionMocks.noManifests)

const useContestsMock = useContests as jest.Mock
jest.mock('../useContests')
useContestsMock.mockImplementation(() => [
  contestMocks.emptyTargeted.contests,
  jest.fn(),
])

const useAuditSettingsMock = useAuditSettings as jest.Mock
jest.mock('../useAuditSettings')
useAuditSettingsMock.mockImplementation(() => [auditSettings.all, jest.fn()])

checkAndToastMock.mockReturnValue(false)

const mockHistoryPush = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: jest.fn(),
  useHistory: () => ({
    push: mockHistoryPush,
  }),
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
    apiMock.mockImplementation(async () => ({ file: null, processing: null }))
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="participants"
          menuItems={relativeStages('participants').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    await screen.findByRole('heading', { name: 'Participants' })
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with locked next stage', async () => {
    apiMock.mockImplementation(async () => ({ file: null, processing: null }))
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="participants"
          menuItems={relativeStages('participants', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    await screen.findByRole('heading', { name: 'Participants' })
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with processing next stage', async () => {
    apiMock.mockImplementation(async () => ({ file: null, processing: null }))
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="participants"
          menuItems={relativeStages('participants', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    await screen.findByRole('heading', { name: 'Participants' })
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="target-contests"
          menuItems={relativeStages('target-contests').menuItems}
        />
      </MemoryRouter>
    )
    screen.getByText('Target Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with locked next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="target-contests"
          menuItems={relativeStages('target-contests', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    screen.getByText('Target Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with processing next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="target-contests"
          menuItems={relativeStages('target-contests', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    screen.getByText('Target Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage', async () => {
    useContestsMock.mockImplementation(() => [
      contestMocks.emptyOpportunistic.contests,
      jest.fn(),
    ])
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="opportunistic-contests"
          menuItems={relativeStages('opportunistic-contests').menuItems}
        />
      </MemoryRouter>
    )
    screen.getByText('Opportunistic Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage with locked next stage', async () => {
    useContestsMock.mockImplementation(() => [
      contestMocks.emptyOpportunistic.contests,
      jest.fn(),
    ])
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="opportunistic-contests"
          menuItems={
            relativeStages('opportunistic-contests', 'locked').menuItems
          }
        />
      </MemoryRouter>
    )
    screen.getByText('Opportunistic Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders Opportunistic Contests stage with processing next stage', async () => {
    useContestsMock.mockImplementation(() => [
      contestMocks.emptyOpportunistic.contests,
      jest.fn(),
    ])
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="opportunistic-contests"
          menuItems={
            relativeStages('opportunistic-contests', 'processing').menuItems
          }
        />
      </MemoryRouter>
    )
    screen.getByText('Opportunistic Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="settings"
          menuItems={relativeStages('settings').menuItems}
        />
      </MemoryRouter>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage with locked next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="settings"
          menuItems={relativeStages('settings', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage with processing next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="settings"
          menuItems={relativeStages('settings', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="review"
          menuItems={relativeStages('review').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    screen.getByText('Review & Launch')
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with locked next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="review"
          menuItems={relativeStages('review', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    screen.getByText('Review & Launch')
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with processing next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="review"
          menuItems={relativeStages('review', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    screen.getByText('Review & Launch')
    expect(container).toMatchSnapshot()
  })
})

import React from 'react'
import { useParams, MemoryRouter } from 'react-router-dom'
import { render, waitFor } from '@testing-library/react'
import { auditSettings } from '../useSetupMenuItems/_mocks'
import * as utilities from '../../utilities'
import Setup from './index'
import relativeStages from './_mocks'
import { contestMocks } from './Contests/_mocks'
import useContests from '../useContests'
import useAuditSettings from '../useAuditSettings'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
apiMock.mockImplementation(async () => {})

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
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Participants"
          menuItems={relativeStages('Participants').menuItems}
        />
      </MemoryRouter>
    )
    expect(container).toMatchSnapshot()
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
  })

  it('renders Participants stage with locked next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Participants"
          menuItems={relativeStages('Participants', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Participants stage with processing next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Participants"
          menuItems={relativeStages('Participants', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Target Contests"
          menuItems={relativeStages('Target Contests').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with locked next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Target Contests"
          menuItems={relativeStages('Target Contests', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Target Contests stage with processing next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Target Contests"
          menuItems={relativeStages('Target Contests', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
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
          stage="Opportunistic Contests"
          menuItems={relativeStages('Opportunistic Contests').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
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
          stage="Opportunistic Contests"
          menuItems={
            relativeStages('Opportunistic Contests', 'locked').menuItems
          }
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
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
          stage="Opportunistic Contests"
          menuItems={
            relativeStages('Opportunistic Contests', 'processing').menuItems
          }
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Audit Settings stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Audit Settings"
          menuItems={relativeStages('Audit Settings').menuItems}
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
          stage="Audit Settings"
          menuItems={relativeStages('Audit Settings', 'locked').menuItems}
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
          stage="Audit Settings"
          menuItems={relativeStages('Audit Settings', 'processing').menuItems}
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
          stage="Review & Launch"
          menuItems={relativeStages('Review & Launch').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with locked next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Review & Launch"
          menuItems={relativeStages('Review & Launch', 'locked').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })

  it('renders Review & Launch stage with processing next stage', async () => {
    const { container } = render(
      <MemoryRouter>
        <Setup
          auditType="BALLOT_POLLING"
          refresh={jest.fn()}
          stage="Review & Launch"
          menuItems={relativeStages('Review & Launch', 'processing').menuItems}
        />
      </MemoryRouter>
    )
    await waitFor(() => expect(apiMock).toHaveBeenCalled())
    expect(container).toMatchSnapshot()
  })
})

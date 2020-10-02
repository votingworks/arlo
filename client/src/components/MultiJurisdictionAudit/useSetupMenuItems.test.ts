import { renderHook, act } from '@testing-library/react-hooks'
import { toast } from 'react-toastify'
import * as utilities from '../utilities'
import useSetupMenuItems from './useSetupMenuItems/index'
import {
  IJurisdictionsFileResponse,
  FileProcessingStatus,
} from './useSetupMenuItems/getJurisdictionFileStatus'
import { roundMocks } from './useSetupMenuItems/_mocks'
import { IRound } from './useRoundsAuditAdmin'

jest.unmock('./useSetupMenuItems/index')

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const generateApiMock = (
  roundReturn: { rounds: IRound[] },
  jurisdictionReturn: IJurisdictionsFileResponse
) => async (
  endpoint: string
): Promise<{ rounds: IRound[] } | IJurisdictionsFileResponse> => {
  switch (endpoint) {
    case '/election/1/jurisdiction/file':
      return jurisdictionReturn
    case '/election/1/round':
    default:
      return roundReturn
  }
}

apiMock.mockImplementation(
  generateApiMock(
    { rounds: roundMocks.empty },
    { file: null, processing: null }
  )
)

afterEach(() => {
  apiMock.mockClear()
})

describe('useSetupMenuItems', () => {
  it('returns initial state', async () => {
    const {
      result: {
        current: [menuItems],
      },
    } = renderHook(() => useSetupMenuItems('Participants', jest.fn(), '1'))
    expect(menuItems).toBeTruthy()
  })

  it('calls the getters', async () => {
    const {
      result: {
        current: [, refresh],
      },
      waitForNextUpdate,
    } = renderHook(() => useSetupMenuItems('Participants', jest.fn(), '1'))
    act(() => refresh())
    await waitForNextUpdate()
    expect(apiMock).toHaveBeenCalledTimes(2)
    act(() => refresh())
    await waitForNextUpdate()
    expect(apiMock).toHaveBeenCalledTimes(4)
  })

  it('locks everything if rounds exist', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        {
          rounds: roundMocks.singleIncomplete,
        },
        { file: null, processing: null }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0].every(i => i.state === 'locked')).toBeTruthy()
  })

  it('handles ERRORED response from /jurisdiction/file api', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        { rounds: roundMocks.empty },
        {
          file: null,
          processing: {
            status: FileProcessingStatus.Errored,
            startedAt: '',
            error: null,
            completedAt: null,
          },
        }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state === 'locked').toBeTruthy()
    expect(result.current[0][3].state === 'locked').toBeTruthy()
  })

  it('handles NULL response from /jurisdiction/file api', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        { rounds: roundMocks.empty },
        {
          file: null,
          processing: {
            status: FileProcessingStatus.Blank,
            startedAt: '',
            error: null,
            completedAt: null,
          },
        }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state === 'locked').toBeTruthy()
    expect(result.current[0][3].state === 'locked').toBeTruthy()
  })

  it('handles PROCESSING response from /jurisdiction/file api', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        { rounds: roundMocks.empty },
        {
          file: null,
          processing: {
            status: FileProcessingStatus.Processing,
            startedAt: '',
            error: null,
            completedAt: null,
          },
        }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state === 'processing').toBeTruthy()
    expect(result.current[0][3].state === 'processing').toBeTruthy()
  })

  it('handles change of PROCESSING to PROCESSED response from /jurisdiction/file api', async () => {
    apiMock
      .mockImplementationOnce(
        generateApiMock(
          { rounds: roundMocks.empty },
          {
            file: null,
            processing: {
              status: FileProcessingStatus.Processing,
              startedAt: '',
              error: null,
              completedAt: null,
            },
          }
        )
      )
      .mockImplementation(
        generateApiMock(
          { rounds: roundMocks.empty },
          {
            file: null,
            processing: {
              status: FileProcessingStatus.Processed,
              startedAt: '',
              error: null,
              completedAt: null,
            },
          }
        )
      )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state).toBe('live')
    expect(result.current[0][3].state).toBe('live')
  })

  it('handles change of PROCESSING to ERRORED response from /jurisdiction/file api', async () => {
    apiMock
      .mockImplementationOnce(
        generateApiMock(
          { rounds: roundMocks.empty },
          {
            file: null,
            processing: {
              status: FileProcessingStatus.Processing,
              startedAt: '',
              error: null,
              completedAt: null,
            },
          }
        )
      )
      .mockImplementation(
        generateApiMock(
          { rounds: roundMocks.empty },
          {
            file: null,
            processing: {
              status: FileProcessingStatus.Errored,
              startedAt: '',
              error: null,
              completedAt: null,
            },
          }
        )
      )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state).toBe('processing')
    expect(result.current[0][3].state).toBe('processing')
  })

  it('handles PROCESSED response from /jurisdiction/file api', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        { rounds: roundMocks.empty },
        {
          file: null,
          processing: {
            status: FileProcessingStatus.Processed,
            startedAt: '',
            error: null,
            completedAt: null,
          },
        }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state === 'live').toBeTruthy()
    expect(result.current[0][3].state === 'live').toBeTruthy()
  })

  it('handles READY_TO_PROCESS response from /jurisdiction/file api', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        { rounds: roundMocks.empty },
        {
          file: null,
          processing: {
            status: FileProcessingStatus.ReadyToProcess,
            startedAt: '',
            error: null,
            completedAt: null,
          },
        }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(result.current[0][2].state === 'processing').toBeTruthy()
    expect(result.current[0][3].state === 'processing').toBeTruthy()
  })

  it('handles background process timeout', async () => {
    const toastSpy = jest.spyOn(toast, 'error').mockImplementation()
    const dateIncrementor = (function* incr() {
      let i = 10
      while (true) {
        i += 130000
        yield i
      }
    })()
    const dateSpy = jest
      .spyOn(Date, 'now')
      .mockImplementation(() => dateIncrementor.next().value)
    apiMock.mockImplementation(
      generateApiMock(
        { rounds: roundMocks.empty },
        {
          file: null,
          processing: {
            status: FileProcessingStatus.Processing,
            startedAt: '',
            error: null,
            completedAt: null,
          },
        }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    expect(apiMock).toHaveBeenCalledTimes(3)
    expect(dateSpy).toHaveBeenCalled()
    expect(toastSpy).toHaveBeenCalledTimes(1)
    expect(result.current[0][2].state === 'processing').toBeTruthy()
    expect(result.current[0][3].state === 'processing').toBeTruthy()
  })
})

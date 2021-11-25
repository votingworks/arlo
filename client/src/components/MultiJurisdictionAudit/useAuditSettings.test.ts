import { renderHook, act } from '@testing-library/react-hooks'
import { waitFor } from '@testing-library/react'
import * as utilities from '../utilities'
import useAuditSettings from './useAuditSettings'
import { auditSettings } from './useSetupMenuItems/_mocks'

// TODO update to withMockFetch instead of apiMock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

apiMock.mockResolvedValue(auditSettings.blank)

afterEach(() => {
  apiMock.mockClear()
})

describe('useAuditSettings', () => {
  it('should return blank values', async () => {
    const {
      result: {
        current: [settings],
      },
      waitForNextUpdate,
    } = renderHook(() => useAuditSettings('1'))

    await waitForNextUpdate()
    expect(settings).toStrictEqual(null)
  })

  it('should POST to update values', async () => {
    // do not test that the values themselves change since this
    // hook does not update its values after POSTing
    apiMock
      .mockResolvedValueOnce(auditSettings.blank)
      .mockResolvedValueOnce(auditSettings.blank)
      .mockResolvedValueOnce({ status: 'ok' })
    const {
      result: {
        current: [, updateSettings],
      },
    } = renderHook(() => useAuditSettings('1'))
    await act(async () => {
      expect(updateSettings(auditSettings.all)).toBeTruthy()
    })

    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(3)
    })
  })

  it('should handle GET error', async () => {
    apiMock.mockResolvedValueOnce(null)
    const {
      result: {
        current: [settings],
      },
    } = renderHook(() => useAuditSettings('1'))

    await waitFor(() => {
      expect(settings).toStrictEqual(null)
    })
  })

  it('should handle PUT error', async () => {
    apiMock
      .mockResolvedValueOnce(auditSettings.blank)
      .mockResolvedValueOnce(auditSettings.blank)
      .mockResolvedValueOnce(null)
    const { result, waitForNextUpdate } = renderHook(() =>
      useAuditSettings('1')
    )
    await waitForNextUpdate()
    const success = await result.current[1](auditSettings.all)

    expect(success).toBeFalsy()
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(3)
      expect(result.current[0]).toStrictEqual(auditSettings.blank)
    })
  })
})

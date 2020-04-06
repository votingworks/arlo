import { renderHook, act } from '@testing-library/react-hooks'
import { wait } from '@testing-library/react'
import * as utilities from '../utilities'
import useSetupMenuItems from './useSetupMenuItems/index'
import { IJurisdictionsFileResponse } from './useSetupMenuItems/getJurisdictionFileStatus'
import { IRound } from '../../types'

jest.unmock('./useSetupMenuItems/index')

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

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
  generateApiMock({ rounds: [] }, { file: null, processing: null })
)
checkAndToastMock.mockReturnValue(false)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('useSetupMenuItems', () => {
  it('returns initial state', () => {
    const {
      result: {
        current: [menuItems],
      },
    } = renderHook(() => useSetupMenuItems('Participants', jest.fn(), '1'))
    expect(menuItems).toBeTruthy()
  })

  it('calls the getters', () => {
    const {
      result: {
        current: [, refresh],
      },
    } = renderHook(() => useSetupMenuItems('Participants', jest.fn(), '1'))
    act(() => refresh())
    expect(apiMock).toHaveBeenCalledTimes(2)
    act(() => refresh())
    expect(apiMock).toHaveBeenCalledTimes(4)
  })

  it('locks everything if rounds exist', async () => {
    apiMock.mockImplementation(
      generateApiMock(
        {
          rounds: [
            // content doesn't matter, just that it has a non-zero length and matches the type
            {
              contests: [
                {
                  endMeasurements: {
                    isComplete: null,
                    pvalue: null,
                  },
                  id: 'contest-1',
                  results: {},
                  sampleSize: 379,
                  sampleSizeOptions: [
                    { size: 269, type: 'ASN', prob: null },
                    { size: 379, prob: 0.8, type: null },
                    { size: 78, prob: null, type: null },
                  ],
                },
              ],
              endedAt: null,
              startedAt: '2019-07-18T16:34:07.000Z',
              id: 'round-1',
            },
          ],
        },
        { file: null, processing: null }
      )
    )
    const { result, waitForNextUpdate } = renderHook(() =>
      useSetupMenuItems('Participants', jest.fn(), '1')
    )
    act(() => result.current[1]())
    await waitForNextUpdate()
    await wait(() =>
      expect(result.current[0].every(i => i.state === 'locked')).toBeTruthy()
    )
  })
})

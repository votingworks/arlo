import getRoundStatus from './getRoundStatus'
import * as utilities from '../../utilities'

// TODO update to withMockFetch instead of apiMock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockResolvedValue(null)

describe('getRoundStatus', () => {
  it('handles api request error', async () => {
    const response = await getRoundStatus('1')
    expect(response).toBeFalsy()
    expect(apiMock).toHaveBeenCalledTimes(1)
  })
})

import { toast } from 'react-toastify'
import getRoundStatus from './getRoundStatus'
import * as utilities from '../../utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockRejectedValue(new Error('Network error'))
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

describe('getRoundStatus', () => {
  it('handles api request error', async () => {
    const response = await getRoundStatus('1')
    expect(response).toBeFalsy()
    expect(apiMock).toHaveBeenCalledTimes(1)
    expect(toastSpy).toHaveBeenCalledTimes(1)
    expect(toastSpy).toHaveBeenCalledWith('Network error')
  })
})

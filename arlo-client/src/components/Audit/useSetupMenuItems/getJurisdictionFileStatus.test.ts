import { toast } from 'react-toastify'
import getJurisdictionFileStatus, {
  FileProcessingStatus,
} from './getJurisdictionFileStatus'
import * as utilities from '../../utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockRejectedValue(new Error('Network error'))
const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

describe('getJurisdictionFileStatus', () => {
  it('handles api request error', async () => {
    const response = await getJurisdictionFileStatus('1')
    expect(response).toBe(FileProcessingStatus.Errored)
    expect(apiMock).toHaveBeenCalledTimes(1)
    expect(toastSpy).toHaveBeenCalledTimes(1)
    expect(toastSpy).toHaveBeenCalledWith('Network error')
  })
})

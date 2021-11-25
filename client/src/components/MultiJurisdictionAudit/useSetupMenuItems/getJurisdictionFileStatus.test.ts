import getJurisdictionFileStatus, {
  FileProcessingStatus,
} from './getJurisdictionFileStatus'
import * as utilities from '../../utilities'

// TODO update to withMockFetch instead of apiMock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockResolvedValue(null)

describe('getJurisdictionFileStatus', () => {
  it('handles api request error', async () => {
    const response = await getJurisdictionFileStatus('1')
    expect(response).toStrictEqual({
      status: FileProcessingStatus.Errored,
    })
    expect(apiMock).toHaveBeenCalledTimes(1)
  })
})

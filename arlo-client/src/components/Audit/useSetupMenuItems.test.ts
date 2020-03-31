import { renderHook } from '@testing-library/react-hooks'
import useSetupMenuItems from './useSetupMenuItems/index'
// import getJurisdictionFileStatus from './useSetupMenuItems/getJurisdictionFileStatus'
// import getRoundStatus from './useSetupMenuItems/getRoundStatus'

jest.unmock('./useSetupMenuItems/index')

// const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
// const getRoundStatusMock = getRoundStatus as jest.Mock

describe('useSetupMenuItems', () => {
  it('returns initial state', async () => {
    const {
      result: {
        current: [menuItems, refresh],
      },
    } = renderHook(() => useSetupMenuItems('Participants', jest.fn(), '1'))
    expect(menuItems).toBeTruthy()
    refresh()
  })
})

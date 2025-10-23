import { describe, expect, it } from 'vitest'
import { prettifyRefreshStatus } from './RefreshTag'

describe('prettifyRefreshStatus', () => {
  it('handles recent values', () => {
    expect(prettifyRefreshStatus(0)).toBe('Will refresh in 5 minutes')
    expect(prettifyRefreshStatus(9000)).toBe('Will refresh in 5 minutes')
  })

  it('handles minute increments', () => {
    expect(prettifyRefreshStatus(60000)).toBe('Will refresh in 4 minutes')
    expect(prettifyRefreshStatus(120000)).toBe('Will refresh in 3 minutes')
    expect(prettifyRefreshStatus(180000)).toBe('Will refresh in 2 minutes')
    expect(prettifyRefreshStatus(240000)).toBe('Will refresh in 1 minute')
  })

  it('handles ten second increments', () => {
    expect(prettifyRefreshStatus(250000)).toBe('Will refresh in 50 seconds')
    expect(prettifyRefreshStatus(260001)).toBe('Will refresh in 40 seconds')
    expect(prettifyRefreshStatus(270001)).toBe('Will refresh in 30 seconds')
    expect(prettifyRefreshStatus(280001)).toBe('Will refresh in 20 seconds')
    expect(prettifyRefreshStatus(290001)).toBe('Will refresh in 10 seconds')
  })
})

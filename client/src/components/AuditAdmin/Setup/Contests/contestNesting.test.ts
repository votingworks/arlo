import { describe, expect, it } from 'vitest'
import nestingParentOptions from './contestNesting'

// Contest B is nested under A, and C under B
const contests = [
  { id: 'a', name: 'Contest A', nestedUnderContestId: '' },
  { id: 'b', name: 'Contest B', nestedUnderContestId: 'a' },
  { id: 'c', name: '', nestedUnderContestId: 'b' },
  { id: 'd', name: 'Contest D', nestedUnderContestId: '' },
]

describe('nestingParentOptions', () => {
  it('offers every other contest, labelled by position and name', () => {
    expect(nestingParentOptions(contests, 3)).toEqual([
      { value: '', label: 'None' },
      { value: 'a', label: 'Contest 1: Contest A' },
      { value: 'b', label: 'Contest 2: Contest B' },
      { value: 'c', label: 'Contest 3' },
    ])
  })

  it('excludes the contest itself and its descendants', () => {
    expect(nestingParentOptions(contests, 0)).toEqual([
      { value: '', label: 'None' },
      { value: 'd', label: 'Contest 4: Contest D' },
    ])
    expect(nestingParentOptions(contests, 1)).toEqual([
      { value: '', label: 'None' },
      { value: 'a', label: 'Contest 1: Contest A' },
      { value: 'd', label: 'Contest 4: Contest D' },
    ])
  })
})

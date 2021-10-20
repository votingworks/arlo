import { sum } from './number'

test('sum', () => {
  expect(sum([])).toEqual(0)
  expect(sum([1, 2, 3])).toEqual(6)
  expect(sum([-1, 2, 3])).toEqual(4)
})

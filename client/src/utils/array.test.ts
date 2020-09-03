import { groupBy, sortBy } from './array'

test('groupBy', () => {
  expect(groupBy([], () => '')).toEqual({})
  expect(groupBy([{ a: '1' }], o => o.a)).toEqual({ '1': [{ a: '1' }] })
  expect(
    groupBy(
      [{ a: '1', b: '1' }, { a: '2', b: '2' }, { a: '1', b: '3' }],
      o => o.a
    )
  ).toEqual({
    '1': [{ a: '1', b: '1' }, { a: '1', b: '3' }],
    '2': [{ a: '2', b: '2' }],
  })
})

test('sortBy', () => {
  expect(sortBy([], () => '')).toEqual([])
  expect(sortBy([2, 1, 3], x => x)).toEqual([1, 2, 3])
  expect(sortBy(['b', 'c', 'a'], x => x)).toEqual(['a', 'b', 'c'])
  expect(sortBy([{ a: 'b' }, { a: 'c' }, { a: 'a' }], x => x.a)).toEqual([
    { a: 'a' },
    { a: 'b' },
    { a: 'c' },
  ])
})

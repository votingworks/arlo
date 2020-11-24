import { groupBy, sortBy, hashBy, replaceAtIndex, range } from './array'

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
  expect(sortBy([2, 1, 3, 2], x => x)).toEqual([1, 2, 2, 3])
  expect(sortBy(['b', 'c', 'a'], x => x)).toEqual(['a', 'b', 'c'])
  expect(sortBy([{ a: 'b' }, { a: 'c' }, { a: 'a' }], x => x.a)).toEqual([
    { a: 'a' },
    { a: 'b' },
    { a: 'c' },
  ])
})

test('hashBy', () => {
  expect(hashBy(null, () => 1)).toEqual(null)
  expect(hashBy([], () => 1)).toEqual('')
  expect(hashBy([2, 1, 3, 2], x => x)).toEqual('2;1;3;2')
  expect(hashBy([{ a: 'b' }, { a: 'c' }, { a: 'a' }], x => x.a)).toEqual(
    'b;c;a'
  )
})

test('replaceAtIndex', () => {
  expect(replaceAtIndex([], 0, 'a')).toEqual(['a'])
  expect(replaceAtIndex(['a'], 0, 'b')).toEqual(['b'])
  expect(replaceAtIndex(['a'], 1, 'b')).toEqual(['a', 'b'])
  expect(replaceAtIndex(['a', 'b'], 0, 'c')).toEqual(['c', 'b'])
  expect(replaceAtIndex(['a', 'b'], 1, 'c')).toEqual(['a', 'c'])
  expect(replaceAtIndex(['a', 'b'], 2, 'c')).toEqual(['a', 'b', 'c'])
  expect(replaceAtIndex(['a', 'b', 'c'], 0, 'd')).toEqual(['d', 'b', 'c'])
  expect(replaceAtIndex(['a', 'b', 'c'], 1, 'd')).toEqual(['a', 'd', 'c'])
  expect(replaceAtIndex(['a', 'b', 'c'], 2, 'd')).toEqual(['a', 'b', 'd'])
  expect(replaceAtIndex(['a', 'b', 'c'], 3, 'd')).toEqual(['a', 'b', 'c', 'd'])
})

test('range', () => {
  expect(range(0, 0)).toEqual([0])
  expect(range(0, 1)).toEqual([0, 1])
  expect(range(0, 2)).toEqual([0, 1, 2])
  expect(range(1, 1)).toEqual([1])
  expect(range(1, 2)).toEqual([1, 2])
  expect(range(1, 3)).toEqual([1, 2, 3])
  expect(range(1, 5)).toEqual([1, 2, 3, 4, 5])
  expect(range(3, 5)).toEqual([3, 4, 5])
})

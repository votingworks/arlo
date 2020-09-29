import { groupBy, sortBy, hashBy } from './array'

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

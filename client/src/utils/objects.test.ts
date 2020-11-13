import { numberifyObject, isObjectEmpty, stringifyObject } from './objects'

test('isObjectEmpty', () => {
  expect(isObjectEmpty({})).toBeTruthy()
  expect(isObjectEmpty({ key: 'value' })).toBeFalsy()
})

test('numberifyObject', () => {
  expect(numberifyObject({})).toDeepEqual({})
  expect(numberifyObject({ a: '1' })).toDeepEqual({ a: 1 })
  expect(numberifyObject({ a: '1', b: '2' })).toDeepEqual({ a: 1, b: 2 })
  expect(numberifyObject({ a: '1,000' })).toDeepEqual({ a: 1000 })
})

test('stringifyObject', () => {
  expect(stringifyObject({})).toDeepEqual({})
  expect(stringifyObject({ a: 1 })).toDeepEqual({ a: '1' })
  expect(stringifyObject({ a: 1, b: 2 })).toDeepEqual({ a: '1', b: '2' })
  expect(stringifyObject({ a: 1000 })).toDeepEqual({ a: '1000' })
  expect(
    stringifyObject({ a: 1 }, (s: string): string => s.repeat(2))
  ).toDeepEqual({ a: '11' })
})

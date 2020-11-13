import { numberifyObject, isObjectEmpty, stringifyObject } from './objects'

test('isObjectEmpty', () => {
  expect(isObjectEmpty({})).toBeTruthy()
  expect(isObjectEmpty({ key: 'value' })).toBeFalsy()
})

test('numberifyObject', () => {
  expect(numberifyObject({})).toEqual({})
  expect(numberifyObject({ a: '1' })).toEqual({ a: 1 })
  expect(numberifyObject({ a: '1', b: '2' })).toEqual({ a: 1, b: 2 })
  expect(numberifyObject({ a: '1,000' })).toEqual({ a: 1000 })
})

test('stringifyObject', () => {
  expect(stringifyObject({})).toEqual({})
  expect(stringifyObject({ a: 1 })).toEqual({ a: '1' })
  expect(stringifyObject({ a: 1, b: 2 })).toEqual({ a: '1', b: '2' })
  expect(stringifyObject({ a: 1000 })).toEqual({ a: '1000' })
  expect(stringifyObject({ a: 1 }, (s: string): string => s.repeat(2))).toEqual(
    { a: '11' }
  )
})

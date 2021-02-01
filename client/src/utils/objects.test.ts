import { isObjectEmpty, mapValues } from './objects'

test('isObjectEmpty', () => {
  expect(isObjectEmpty({})).toBeTruthy()
  expect(isObjectEmpty({ key: 'value' })).toBeFalsy()
})

test('mapValues', () => {
  expect(mapValues({}, () => 1)).toEqual({})
  expect(mapValues({ a: 1, b: 2 }, v => v + 1)).toEqual({ a: 2, b: 3 })
  expect(mapValues({ a: 1, b: 2 }, (v, k) => v + k)).toEqual({
    a: '1a',
    b: '2b',
  })
})

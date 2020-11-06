import isObjectEmpty from './objects'

test('isObjectEmpty', () => {
  expect(isObjectEmpty({})).toBeTruthy()
  expect(isObjectEmpty({ key: 'value' })).toBeFalsy()
})

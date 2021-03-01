import { pluralize } from './string'

test('pluralize', () => {
  expect(pluralize('word', 0)).toEqual('words')
  expect(pluralize('word', 1)).toEqual('word')
  expect(pluralize('word', 2)).toEqual('words')
  expect(pluralize('word', 3)).toEqual('words')
})
